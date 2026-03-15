'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { creditApi } from '@/lib/api';

export function useCreditReports(clientId?: string) {
  return useQuery({
    queryKey: ['credit-reports', clientId],
    queryFn: () => creditApi.listReports(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useCreateCreditReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ clientId, documentId }: { clientId: string; documentId?: string }) =>
      creditApi.createReport(clientId, documentId).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-reports'] }),
  });
}

export function useTradelines(reportId?: string) {
  return useQuery({
    queryKey: ['credit-tradelines', reportId],
    queryFn: () => creditApi.getTradelines(reportId!).then((r) => r.data),
    enabled: Boolean(reportId),
  });
}

export function useCollections(reportId?: string) {
  return useQuery({
    queryKey: ['credit-collections', reportId],
    queryFn: () => creditApi.getCollections(reportId!).then((r) => r.data),
    enabled: Boolean(reportId),
  });
}

export function useDisputes(clientId?: string) {
  return useQuery({
    queryKey: ['credit-disputes', clientId],
    queryFn: () => creditApi.listDisputes(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useCreateDispute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      client_id: string;
      bureau: string;
      furnisher?: string;
      issue_type: string;
      notes_json?: Record<string, unknown>;
    }) => creditApi.createDispute(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-disputes'] }),
  });
}

export function useUpdateDispute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      disputeId,
      data,
    }: {
      disputeId: string;
      data: { status?: string; notes_json?: Record<string, unknown> };
    }) => creditApi.updateDispute(disputeId, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-disputes'] }),
  });
}

export function useGenerateDisputeLetter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (disputeId: string) =>
      creditApi.generateLetter(disputeId).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dispute-letters'] }),
  });
}

export function useDisputeLetters(disputeId?: string) {
  return useQuery({
    queryKey: ['dispute-letters', disputeId],
    queryFn: () => creditApi.listLetters(disputeId!).then((r) => r.data),
    enabled: Boolean(disputeId),
  });
}

export function useCreditHealth(clientId?: string) {
  return useQuery({
    queryKey: ['credit-health', clientId],
    queryFn: () => creditApi.getHealth(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}
