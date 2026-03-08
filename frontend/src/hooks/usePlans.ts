'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { plansApi } from '@/lib/api';

export function usePlans(clientId?: string) {
  return useQuery({
    queryKey: ['plans', clientId],
    queryFn: () => plansApi.list(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}

export function usePlan(planId?: string) {
  return useQuery({
    queryKey: ['plan', planId],
    queryFn: () => plansApi.get(planId!).then((r) => r.data),
    enabled: Boolean(planId),
  });
}

export function useGeneratePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { client_id: string; goal?: string; time_horizon_days?: number }) =>
      plansApi.generate(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plans'] }),
  });
}

export function usePublishPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => plansApi.publish(planId).then((r) => r.data),
    onSuccess: (_, planId) => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['plan', planId] });
    },
  });
}

export function useUpdatePlanAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      planId,
      actionId,
      status,
    }: {
      planId: string;
      actionId: string;
      status: string;
    }) => plansApi.updateAction(planId, actionId, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plans'] });
      qc.invalidateQueries({ queryKey: ['plan'] });
    },
  });
}

export function useScores(clientId?: string) {
  return useQuery({
    queryKey: ['scores', clientId],
    queryFn: () => plansApi.getScores(clientId!).then((r) => r.data),
    enabled: Boolean(clientId),
  });
}
