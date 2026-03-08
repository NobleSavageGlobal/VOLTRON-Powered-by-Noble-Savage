'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { financialApi } from '@/lib/api';

export function useFinancialConnections(clientId?: string) {
  return useQuery({
    queryKey: ['financial-connections', clientId],
    queryFn: () => financialApi.listConnections(clientId).then((r) => r.data),
  });
}

export function useCreateConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { client_id: string; provider: string; account_mask?: string }) =>
      financialApi.createConnection(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial-connections'] }),
  });
}

export function useSyncConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      financialApi.syncConnection(connectionId).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['financial-connections'] });
      qc.invalidateQueries({ queryKey: ['financial-transactions'] });
      qc.invalidateQueries({ queryKey: ['financial-rollups'] });
      qc.invalidateQueries({ queryKey: ['financial-summary'] });
    },
  });
}

export function useTransactions(clientId?: string) {
  return useQuery({
    queryKey: ['financial-transactions', clientId],
    queryFn: () =>
      financialApi.listTransactions({ client_id: clientId }).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useMonthlyRollups(clientId?: string) {
  return useQuery({
    queryKey: ['financial-rollups', clientId],
    queryFn: () => financialApi.getRollups(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useFinancialSummary(clientId?: string) {
  return useQuery({
    queryKey: ['financial-summary', clientId],
    queryFn: () => financialApi.getSummary(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useObligations(clientId?: string) {
  return useQuery({
    queryKey: ['financial-obligations', clientId],
    queryFn: () => financialApi.listObligations(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function useCreateObligation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      client_id: string;
      obligation_type: string;
      creditor_name?: string;
      principal?: number;
      monthly_payment?: number;
      apr?: number;
      balance?: number;
      status?: string;
      notes?: string;
    }) => financialApi.createObligation(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['financial-obligations'] });
      qc.invalidateQueries({ queryKey: ['financial-summary'] });
    },
  });
}
