import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Document,
  Organization,
  PaginatedResponse,
  Task,
  TokenResponse,
  User,
  AuditEntry,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason?: unknown) => void;
}> = [];

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
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
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
        typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

      if (!refreshToken) {
        processQueue(error);
        isRefreshing = false;
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        const resp = await axios.post<TokenResponse>(
          `${BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );
        const { access_token, refresh_token: newRefresh } = resp.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', newRefresh);
        processQueue(null, access_token);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    org_name?: string;
  }) => apiClient.post<User>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>('/auth/login', data),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }),

  logout: () => apiClient.post('/auth/logout'),

  me: () => apiClient.get<User>('/auth/me'),
};

// Documents
export const documentsApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post<Document>('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  list: (params?: {
    status?: string;
    doc_type?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<Document>>('/documents/', { params }),

  get: (id: string) => apiClient.get<Document>(`/documents/${id}`),

  update: (id: string, data: { status?: string; notes?: string; doc_type?: string }) =>
    apiClient.patch<Document>(`/documents/${id}`, data),

  delete: (id: string) => apiClient.delete(`/documents/${id}`),

  reprocess: (id: string) => apiClient.post<Document>(`/documents/${id}/reprocess`),
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
  }) => apiClient.post<Task>('/tasks/', data),

  list: (params?: {
    status?: string;
    priority?: string;
    assigned_to?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<Task>>('/tasks/', { params }),

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
    }
  ) => apiClient.patch<Task>(`/tasks/${id}`, data),

  delete: (id: string) => apiClient.delete(`/tasks/${id}`),
};

// Organizations
export const orgsApi = {
  getMe: () => apiClient.get<Organization>('/organizations/me'),
  updateMe: (data: { name?: string; plan?: string }) =>
    apiClient.patch<Organization>('/organizations/me', data),
  listMembers: () => apiClient.get<User[]>('/organizations/me/members'),
};

// Audit
export const auditApi = {
  list: (params?: {
    action?: string;
    resource_type?: string;
    page?: number;
    page_size?: number;
  }) => apiClient.get<PaginatedResponse<AuditEntry>>('/audit/', { params }),
};

export default apiClient;
