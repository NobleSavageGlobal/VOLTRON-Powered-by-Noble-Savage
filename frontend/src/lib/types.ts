export type UserRole = 'admin' | 'advisor' | 'entrepreneur';
export type DocumentStatus = 'pending' | 'processing' | 'processed' | 'failed' | 'review_required';
export type DocumentType =
  | 'bank_statement'
  | 'tax_return'
  | 'contract'
  | 'invoice'
  | 'credit_report'
  | 'government'
  | 'other';
export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'review' | 'done';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';
export type TaskSource = 'manual' | 'ai_generated' | 'automation';
export type ClientStatus = 'active' | 'inactive';
export type ClientEntityType = 'person' | 'business' | 'trust' | 'other';

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
