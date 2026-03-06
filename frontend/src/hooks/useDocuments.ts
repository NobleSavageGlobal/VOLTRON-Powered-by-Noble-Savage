'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '@/lib/api';
import type { Document, PaginatedResponse } from '@/lib/types';

export function useDocuments(params?: {
  status?: string;
  doc_type?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: async () => {
      const resp = await documentsApi.list(params);
      return resp.data as PaginatedResponse<Document>;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const resp = await documentsApi.get(id);
      return resp.data as Document;
    },
    enabled: Boolean(id),
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => documentsApi.upload(file).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}

export function useReprocessDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.reprocess(id).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['documents'] });
      qc.invalidateQueries({ queryKey: ['document', id] });
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });
}
