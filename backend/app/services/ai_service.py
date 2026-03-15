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
- extracted_data: object with relevant key-value pairs extracted from the document.
    Include onboarding-friendly keys when possible:
    - candidate_client_name: string
    - entity_type: one of [person, business, trust, other]
    - industry: string
    - annual_revenue_range: one of [Under $50K, $50K-$100K, $100K-$250K, $250K-$500K, $500K-$1M, Over $1M]
    - ein: string formatted 12-3456789
    - ssn_last4: string of 4 digits
    - contact_email: string
    - contact_phone: string
    - monetary_values: object of important amounts if present

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

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
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
            "bank_statement",
            "tax_return",
            "contract",
            "invoice",
            "credit_report",
            "government",
            "other",
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
        if not isinstance(result["extracted_data"], dict):
            result["extracted_data"] = {}
        if not isinstance(result["key_dates"], list):
            result["key_dates"] = []
        if not isinstance(result["risks"], list):
            result["risks"] = []
        if not isinstance(result["opportunities"], list):
            result["opportunities"] = []
        return result

    async def compute_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not settings.OPENAI_API_KEY:
            return [[] for _ in texts]

        client = self._get_client()
        safe_texts = [text[:6000].replace("```", "'''") for text in texts]

        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=safe_texts,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning("Embedding generation failed", error=str(exc))
            return [[] for _ in texts]

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
                    {
                        "role": "user",
                        "content": f"Based on this context, generate tasks:\n{safe_context}",
                    },
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

    async def generate_decision_plan(
        self,
        snapshot: dict[str, Any],
        context_docs: list[dict[str, Any]],
        goal: str,
    ) -> dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OPENAI_API_KEY not configured")

        client = self._get_client()
        safe_goal = goal[:500].replace("```", "'''")
        safe_snapshot = json.dumps(snapshot, default=str)[:3000]

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strategic financial advisor AI. Generate a decision plan for a client. "
                            "Respond with JSON: {plan_title: str, actions: [{id: str, type: str, title: str, "
                            "why: str, depends_on: [str], due_in_days: int, success_metric: str, "
                            "evidence_refs: [str], risk_flags: [str]}]}. Be specific and actionable."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Goal: {safe_goal}\nClient snapshot: {safe_snapshot}",
                    },
                ],
                temperature=0.2,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            logger.error("Decision plan generation failed", error=str(exc))
            raise AIServiceError(f"Failed to generate decision plan: {exc}") from exc
