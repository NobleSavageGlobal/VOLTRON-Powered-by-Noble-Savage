import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import type {
  Client,
  CreditHealth,
  CreditReport,
  DecisionPlan,
  Dispute,
  DisputeLetter,
  DocumentBatchUploadResponse,
  Document,
  FinancialConnection,
  FinancialSummary,
  FinancialTransaction,
  KnowledgeChunk,
  KnowledgeSearchResult,
  MonthlyRollup,
  Obligation,
  Organization,
  PaginatedResponse,
  ScoringSnapshot,
  Task,
  TokenResponse,
  Tradeline,
  CollectionItem,
  User,
  AuditEntry,
  Workflow,
  WorkflowRun,
  AutomationEvent,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason?: unknown) => void;
}> = [];

const RETRYABLE_METHODS = new Set(["get", "head", "options"]);
const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);
const MAX_RETRY_ATTEMPTS = 2;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getRetryDelay(attempt: number): number {
  const base = 400;
  const jitter = Math.floor(Math.random() * 120);
  return base * Math.pow(2, attempt) + jitter;
}

function isRetryableRequest(
  error: AxiosError,
  request: InternalAxiosRequestConfig & {
    _networkRetryCount?: number;
    _retry?: boolean;
  },
): boolean {
  const method = (request.method ?? "get").toLowerCase();
  if (!RETRYABLE_METHODS.has(method)) {
    return false;
  }

  const url = request.url ?? "";
  if (url.includes("/auth/refresh")) {
    return false;
  }

  if (!error.response) {
    return true;
  }

  return RETRYABLE_STATUS_CODES.has(error.response.status);
}

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });
  failedQueue = [];
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
      _networkRetryCount?: number;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken =
        typeof window !== "undefined"
          ? localStorage.getItem("refresh_token")
          : null;

      if (!refreshToken) {
        processQueue(error);
        isRefreshing = false;
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        const resp = await axios.post<TokenResponse>(
          `${BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
        );
        const { access_token, refresh_token: newRefresh } = resp.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", newRefresh);
        processQueue(null, access_token);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (originalRequest && isRetryableRequest(error, originalRequest)) {
      const retryCount = originalRequest._networkRetryCount ?? 0;
      if (retryCount < MAX_RETRY_ATTEMPTS) {
        originalRequest._networkRetryCount = retryCount + 1;
        await wait(getRetryDelay(retryCount));
        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  },
);

// Auth
export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    org_name?: string;
  }) => apiClient.post<User>("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>("/auth/login", data),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    }),

  logout: () => apiClient.post("/auth/logout"),

  me: () => apiClient.get<User>("/auth/me"),
};

// Documents
export const documentsApi = {
  upload: (
    file: File,
    options?: {
      autoOnboard?: boolean;
      clientId?: string;
    },
  ) => {
    const form = new FormData();
    form.append("file", file);
    if (options?.autoOnboard) {
      form.append("auto_onboard", "true");
    }
    if (options?.clientId) {
      form.append("client_id", options.clientId);
    }
    return apiClient.post<Document>("/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  uploadBatch: (
    files: File[],
    options?: {
      autoOnboard?: boolean;
      clientId?: string;
    },
  ) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    if (options?.autoOnboard) {
      form.append("auto_onboard", "true");
    }
    if (options?.clientId) {
      form.append("client_id", options.clientId);
    }
    return apiClient.post<DocumentBatchUploadResponse>(
      "/documents/upload/batch",
      form,
      {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      },
    );
  },

  list: (params?: {
    status?: string;
    doc_type?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<Document>>("/documents/", { params }),

  get: (id: string) => apiClient.get<Document>(`/documents/${id}`),

  update: (
    id: string,
    data: { status?: string; notes?: string; doc_type?: string },
  ) => apiClient.patch<Document>(`/documents/${id}`, data),

  delete: (id: string) => apiClient.delete(`/documents/${id}`),

  reprocess: (id: string) =>
    apiClient.post<Document>(`/documents/${id}/reprocess`),

  autoOnboard: (documentId: string, clientId?: string) =>
    apiClient.post<Document>(`/documents/${documentId}/auto-onboard`, null, {
      params: clientId ? { client_id: clientId } : undefined,
    }),
};

// Tasks
export const tasksApi = {
  create: (data: {
    title: string;
    description?: string;
    status?: string;
    priority?: string;
    due_date?: string;
    assigned_to?: string;
    source?: string;
  }) => apiClient.post<Task>("/tasks/", data),

  list: (params?: {
    status?: string;
    priority?: string;
    assigned_to?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<Task>>("/tasks/", { params }),

  get: (id: string) => apiClient.get<Task>(`/tasks/${id}`),

  update: (
    id: string,
    data: {
      title?: string;
      description?: string;
      status?: string;
      priority?: string;
      due_date?: string;
      assigned_to?: string;
    },
  ) => apiClient.patch<Task>(`/tasks/${id}`, data),

  delete: (id: string) => apiClient.delete(`/tasks/${id}`),
};

// Clients
export const clientsApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiClient.get<Client[]>("/clients/", { params }),

  create: (data: {
    display_name: string;
    entity_type?: string;
    industry?: string;
    annual_revenue_range?: string;
  }) => apiClient.post<Client>("/clients/", data),

  get: (id: string) => apiClient.get<Client>(`/clients/${id}`),

  update: (
    id: string,
    data: {
      display_name?: string;
      entity_type?: string;
      industry?: string;
      annual_revenue_range?: string;
      status?: string;
    },
  ) => apiClient.patch<Client>(`/clients/${id}`, data),

  delete: (id: string) => apiClient.delete(`/clients/${id}`),
};

// Organizations
export const orgsApi = {
  getMe: () => apiClient.get<Organization>("/organizations/me"),
  updateMe: (data: { name?: string; plan?: string }) =>
    apiClient.patch<Organization>("/organizations/me", data),
  listMembers: () => apiClient.get<User[]>("/organizations/me/members"),
};

// Audit
export const auditApi = {
  list: (params?: {
    action?: string;
    resource_type?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<AuditEntry>>("/audit/", { params }),
};

// Financial
export const financialApi = {
  listConnections: (clientId?: string) =>
    apiClient.get<FinancialConnection[]>("/financial/connections", {
      params: clientId ? { client_id: clientId } : undefined,
    }),

  createConnection: (data: {
    client_id: string;
    provider: string;
    account_mask?: string;
  }) => apiClient.post<FinancialConnection>("/financial/connections", data),

  syncConnection: (connectionId: string) =>
    apiClient.post<{ transactions_created: number; connection_id: string }>(
      `/financial/connections/${connectionId}/sync`,
    ),

  listTransactions: (params?: {
    client_id?: string;
    limit?: number;
    offset?: number;
  }) =>
    apiClient.get<FinancialTransaction[]>("/financial/transactions", {
      params,
    }),

  getRollups: (clientId: string) =>
    apiClient.get<MonthlyRollup[]>("/financial/rollups", {
      params: { client_id: clientId },
    }),

  getSummary: (clientId: string) =>
    apiClient.get<FinancialSummary>("/financial/summary", {
      params: { client_id: clientId },
    }),

  listObligations: (clientId: string) =>
    apiClient.get<Obligation[]>("/financial/obligations", {
      params: { client_id: clientId },
    }),

  createObligation: (data: {
    client_id: string;
    obligation_type: string;
    creditor_name?: string;
    principal?: number;
    monthly_payment?: number;
    apr?: number;
    balance?: number;
    status?: string;
    notes?: string;
  }) => apiClient.post<Obligation>("/financial/obligations", data),
};

// Credit
export const creditApi = {
  listReports: (clientId: string) =>
    apiClient.get<CreditReport[]>("/credit/reports", {
      params: { client_id: clientId },
    }),

  createReport: (clientId: string, documentId?: string) =>
    apiClient.post<CreditReport>("/credit/reports", null, {
      params: { client_id: clientId, document_id: documentId },
    }),

  getTradelines: (reportId: string) =>
    apiClient.get<Tradeline[]>(`/credit/reports/${reportId}/tradelines`),

  getCollections: (reportId: string) =>
    apiClient.get<CollectionItem[]>(`/credit/reports/${reportId}/collections`),

  listDisputes: (clientId: string) =>
    apiClient.get<Dispute[]>("/credit/disputes", {
      params: { client_id: clientId },
    }),

  createDispute: (data: {
    client_id: string;
    bureau: string;
    furnisher?: string;
    issue_type: string;
    notes_json?: Record<string, unknown>;
  }) => apiClient.post<Dispute>("/credit/disputes", data),

  updateDispute: (
    disputeId: string,
    data: { status?: string; notes_json?: Record<string, unknown> },
  ) => apiClient.patch<Dispute>(`/credit/disputes/${disputeId}`, data),

  generateLetter: (disputeId: string) =>
    apiClient.post<DisputeLetter>(`/credit/disputes/${disputeId}/letters`),

  listLetters: (disputeId: string) =>
    apiClient.get<DisputeLetter[]>(`/credit/disputes/${disputeId}/letters`),

  getHealth: (clientId: string) =>
    apiClient.get<CreditHealth>("/credit/health", {
      params: { client_id: clientId },
    }),
};

// Plans / Decision
export const plansApi = {
  list: (clientId: string) =>
    apiClient.get<DecisionPlan[]>("/plans/", {
      params: { client_id: clientId },
    }),

  generate: (data: {
    client_id: string;
    goal?: string;
    time_horizon_days?: number;
  }) => apiClient.post<DecisionPlan>("/plans/generate", data),

  get: (planId: string) => apiClient.get<DecisionPlan>(`/plans/${planId}`),

  publish: (planId: string) =>
    apiClient.post<DecisionPlan>(`/plans/${planId}/publish`),

  updateAction: (
    planId: string,
    actionId: string,
    data: { status?: string },
  ) => apiClient.patch(`/plans/${planId}/actions/${actionId}`, data),

  getScores: (clientId: string) =>
    apiClient.get<ScoringSnapshot[]>("/plans/scores/latest", {
      params: { client_id: clientId },
    }),
};

// Automations
export const automationsApi = {
  listWorkflows: () => apiClient.get<Workflow[]>("/automations/workflows"),

  createWorkflow: (data: {
    name: string;
    trigger_type: string;
    trigger_config: Record<string, unknown>;
    actions: Record<string, unknown>[];
  }) => apiClient.post<Workflow>("/automations/workflows", data),

  updateWorkflow: (
    workflowId: string,
    data: {
      name?: string;
      trigger_type?: string;
      trigger_config?: Record<string, unknown>;
      actions?: Record<string, unknown>[];
      status?: string;
    },
  ) => apiClient.patch<Workflow>(`/automations/workflows/${workflowId}`, data),

  runWorkflow: (workflowId: string) =>
    apiClient.post<WorkflowRun>(`/automations/workflows/${workflowId}/run`),

  listRuns: (params?: { limit?: number }) =>
    apiClient.get<WorkflowRun[]>("/automations/runs", { params }),

  listEvents: (params?: { limit?: number }) =>
    apiClient.get<AutomationEvent[]>("/automations/events", { params }),
};

// Knowledge
export const knowledgeApi = {
  search: (params: {
    q: string;
    client_id?: string;
    limit?: number;
  }) =>
    apiClient.get<KnowledgeSearchResult[]>("/knowledge/search", { params }),

  indexDocument: (documentId: string, clientId?: string) =>
    apiClient.post<{ indexed_chunks: number; document_id: string }>(
      "/knowledge/index",
      null,
      { params: { document_id: documentId, client_id: clientId } },
    ),

  listChunks: (params?: { client_id?: string; limit?: number }) =>
    apiClient.get<KnowledgeChunk[]>("/knowledge/chunks", { params }),
};

export const healthApi = {
  ping: () =>
    axios.get<{ status: string; service: string; environment: string }>(
      `${BASE_URL}/health`,
      { timeout: 5000 },
    ),
};

export default apiClient;
