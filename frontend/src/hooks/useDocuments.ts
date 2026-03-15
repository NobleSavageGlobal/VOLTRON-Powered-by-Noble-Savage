"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";
import type {
  Document,
  DocumentBatchUploadResponse,
  PaginatedResponse,
} from "@/lib/types";

export function useDocuments(params?: {
  status?: string;
  doc_type?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: async () => {
      const resp = await documentsApi.list(params);
      return resp.data as PaginatedResponse<Document>;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ["document", id],
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
    mutationFn: ({
      file,
      autoOnboard,
      clientId,
    }: {
      file: File;
      autoOnboard?: boolean;
      clientId?: string;
    }) =>
      documentsApi
        .upload(file, {
          autoOnboard,
          clientId,
        })
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useBatchUploadDocuments() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      files,
      autoOnboard,
      clientId,
    }: {
      files: File[];
      autoOnboard?: boolean;
      clientId?: string;
    }) =>
      documentsApi
        .uploadBatch(files, {
          autoOnboard,
          clientId,
        })
        .then((r) => r.data as DocumentBatchUploadResponse),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

export function useReprocessDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.reprocess(id).then((r) => r.data),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["document", id] });
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useAutoOnboardDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      documentId,
      clientId,
    }: {
      documentId: string;
      clientId?: string;
    }) => documentsApi.autoOnboard(documentId, clientId).then((r) => r.data),
    onSuccess: (_, { documentId }) => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["document", documentId] });
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}
