export type UserRole = "admin" | "advisor" | "entrepreneur";
export type DocumentStatus =
  | "pending"
  | "processing"
  | "processed"
  | "failed"
  | "review_required";
export type DocumentType =
  | "bank_statement"
  | "tax_return"
  | "contract"
  | "invoice"
  | "credit_report"
  | "government"
  | "other";
export type TaskStatus = "todo" | "in_progress" | "blocked" | "review" | "done";
export type TaskPriority = "critical" | "high" | "medium" | "low";
export type TaskSource = "manual" | "ai_generated" | "automation";
export type ClientStatus = "active" | "inactive";
export type ClientEntityType = "person" | "business" | "trust" | "other";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  org_id: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
  updated_at: string;
  settings: Record<string, unknown>;
}

export interface Document {
  id: string;
  org_id: string;
  client_id: string | null;
  uploaded_by: string | null;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  doc_type: DocumentType;
  confidence_score: number | null;
  ai_summary: string | null;
  key_dates: KeyDate[] | null;
  risks: string[] | null;
  opportunities: string[] | null;
  extracted_data: Record<string, unknown> | null;
  notes: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface DocumentUploadResult {
  filename: string;
  success: boolean;
  document: Document | null;
  error: string | null;
}

export interface DocumentBatchUploadResponse {
  items: DocumentUploadResult[];
  success_count: number;
  failure_count: number;
}

export interface KeyDate {
  date: string;
  description: string;
}

export interface Task {
  id: string;
  org_id: string;
  created_by: string | null;
  assigned_to: string | null;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  completed_at: string | null;
  source: TaskSource;
  metadata_: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  org_id: string | null;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  timestamp: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  detail: string;
}

export interface Client {
  id: string;
  org_id: string;
  display_name: string;
  entity_type: ClientEntityType;
  industry: string | null;
  annual_revenue_range: string | null;
  profile_json: Record<string, unknown> | null;
  status: ClientStatus;
  created_at: string;
  updated_at: string;
}

// --- Financial ---

export interface FinancialConnection {
  id: string;
  client_id: string;
  provider: string;
  account_mask: string | null;
  status: string;
  last_synced_at: string | null;
  created_at: string;
}

export interface FinancialTransaction {
  id: string;
  account_id: string;
  posted_at: string;
  amount: number;
  description: string;
  merchant: string | null;
  category: string | null;
  transaction_type: string;
  hash_dedupe: string;
  created_at: string;
}

export interface MonthlyRollup {
  id: string;
  client_id: string;
  period_month: string;
  income_total: number;
  expense_total: number;
  net_total: number;
  category_breakdown: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

export interface Obligation {
  id: string;
  client_id: string;
  obligation_type: string;
  creditor_name: string | null;
  principal: number | null;
  monthly_payment: number | null;
  apr: number | null;
  balance: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinancialSummary {
  client_id: string;
  total_income_3mo: number;
  total_expenses_3mo: number;
  net_3mo: number;
  avg_monthly_income: number;
  avg_monthly_expenses: number;
  obligations_count: number;
  obligations_total_monthly: number;
  recent_rollups: MonthlyRollup[];
}

// --- Credit ---

export interface CreditReport {
  id: string;
  client_id: string;
  source: string;
  report_date: string | null;
  status: string;
  bureaus: string[] | null;
  created_at: string;
  tradelines_count: number;
  collections_count: number;
}

export interface Tradeline {
  id: string;
  creditor_name: string;
  account_type: string;
  balance: number | null;
  payment_status: string | null;
}

export interface CollectionItem {
  id: string;
  collector_name: string | null;
  amount: number | null;
  status: string | null;
}

export interface Dispute {
  id: string;
  client_id: string;
  bureau: string;
  furnisher: string | null;
  issue_type: string;
  status: string;
  created_at: string;
  sent_at: string | null;
  expected_response_by: string | null;
  resolved_at: string | null;
  notes_json: Record<string, unknown> | null;
}

export interface DisputeLetter {
  id: string;
  dispute_id: string;
  template_version: string;
  content_text: string;
  created_by: string;
  created_at: string;
}

export interface CreditHealth {
  derogatory_count: number;
  utilization_avg: number;
  collection_total: number;
}

// --- Plans / Decision ---

export interface PlanAction {
  id: string;
  action_code: string;
  action_type: string;
  title: string;
  description: string | null;
  why: string | null;
  depends_on: string[] | null;
  due_in_days: number | null;
  success_metric: string | null;
  evidence_refs: string[] | null;
  risk_flags: string[] | null;
  status: string;
  created_at: string;
}

export interface DecisionPlan {
  id: string;
  client_id: string;
  plan_title: string;
  plan_version: number;
  status: string;
  goal: string | null;
  time_horizon_days: number | null;
  created_at: string;
  published_at: string | null;
  actions: PlanAction[];
}

export interface ScoringSnapshot {
  id: string;
  client_id: string;
  score_type: string;
  score: number;
  factors_json: Record<string, unknown> | null;
  computed_at: string;
}

// --- Automations ---

export interface Workflow {
  id: string;
  org_id: string;
  name: string;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  actions: Record<string, unknown>[];
  status: string;
  run_count: number;
  last_triggered_at: string | null;
  created_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: string;
  trigger_event: Record<string, unknown> | null;
  started_at: string;
  completed_at: string | null;
  error_json: Record<string, unknown> | null;
}

export interface AutomationEvent {
  id: string;
  org_id: string;
  event_type: string;
  payload_json: Record<string, unknown> | null;
  processed: boolean;
  created_at: string;
}

// --- Knowledge ---

export interface KnowledgeChunk {
  id: string;
  document_id: string | null;
  chunk_text: string;
  chunk_index: number;
  created_at: string;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  document_id: string | null;
  text: string;
  score: number;
  page: number | null;
}
