from __future__ import annotations

import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """You are a financial document analyst AI assistant.
Your task is to analyze document text and extract structured information.
Always respond with valid JSON matching the requested schema exactly.
Never deviate from the schema or add extra keys.
Do not include instructions, commentary, or any user-controllable text in system logic paths."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following document and return a JSON object with these exact fields:
- doc_type: one of [bank_statement, tax_return, contract, invoice, credit_report, government, other]
- confidence_score: float 0.0-1.0 indicating classification confidence
- summary: string, 2-4 sentence summary of the document
- key_dates: array of objects with {date: "YYYY-MM-DD", description: string}
- risks: array of strings describing potential risks
- opportunities: array of strings describing potential opportunities
- extracted_data: object with relevant key-value pairs extracted from the document

Document filename: {filename}
Initial classification hint: {doc_type}

Document text (truncated to 4000 chars):
{text}

Respond ONLY with the JSON object, no other text."""


class AIService:
    def __init__(self) -> None:
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError as exc:
                raise AIServiceError("openai package not installed") from exc
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_document(
        self,
        text: str,
        filename: str,
        doc_type: str,
    ) -> dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OPENAI_API_KEY not configured")

        client = self._get_client()

        # Sanitize user-controlled text before including in user message
        safe_text = text[:4000].replace("```", "'''")
        safe_filename = filename[:256].replace("\n", " ").replace("\r", " ")

        user_message = ANALYSIS_PROMPT_TEMPLATE.format(
            filename=safe_filename,
            doc_type=doc_type,
            text=safe_text,
        )

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            return self._validate_result(result)
        except json.JSONDecodeError as exc:
            logger.error("AI service returned invalid JSON", error=str(exc))
            raise AIServiceError("AI service returned invalid JSON") from exc
        except Exception as exc:
            logger.error("AI service call failed", error=str(exc))
            raise AIServiceError(f"AI service error: {exc}") from exc

    def _validate_result(self, result: dict[str, Any]) -> dict[str, Any]:
        valid_doc_types = {
            "bank_statement", "tax_return", "contract", "invoice",
            "credit_report", "government", "other"
        }
        if result.get("doc_type") not in valid_doc_types:
            result["doc_type"] = "other"

        score = result.get("confidence_score", 0.5)
        if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
            result["confidence_score"] = 0.5

        result.setdefault("summary", "")
        result.setdefault("key_dates", [])
        result.setdefault("risks", [])
        result.setdefault("opportunities", [])
        result.setdefault("extracted_data", {})
        return result

    async def generate_action_plan(self, context: str) -> list[dict[str, Any]]:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OPENAI_API_KEY not configured")

        client = self._get_client()
        safe_context = context[:6000].replace("```", "'''")

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a business advisor AI. Generate actionable tasks for entrepreneurs. "
                            "Respond with a JSON array of task objects with keys: title, description, priority, due_days."
                        ),
                    },
                    {"role": "user", "content": f"Based on this context, generate tasks:\n{safe_context}"},
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or '{"tasks": []}'
            data = json.loads(content)
            return data.get("tasks", [])
        except Exception as exc:
            logger.error("Action plan generation failed", error=str(exc))
            raise AIServiceError(f"Failed to generate action plan: {exc}") from exc
