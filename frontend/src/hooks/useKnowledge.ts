'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '@/lib/api';

export function useKnowledgeSearch(query: string, options?: { limit?: number }) {
  return useQuery({
    queryKey: ['knowledge-search', query, options?.limit],
    queryFn: () =>
      knowledgeApi.search({ query, limit: options?.limit }).then((r) => r.data),
    enabled: query.length > 0,
  });
}

export function useIndexDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) =>
      knowledgeApi.indexDocument(documentId).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge-search'] }),
  });
}

export function useKnowledgeChunks(documentId: string) {
  return useQuery({
    queryKey: ['knowledge-chunks', documentId],
    queryFn: () => knowledgeApi.listChunks(documentId).then((r) => r.data),
    enabled: !!documentId,
  });
}
