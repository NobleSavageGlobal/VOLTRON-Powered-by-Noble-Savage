'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { automationsApi } from '@/lib/api';

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => automationsApi.listWorkflows().then((r) => r.data),
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      trigger_type: string;
      trigger_config: Record<string, unknown>;
      actions: Record<string, unknown>[];
    }) => automationsApi.createWorkflow(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  });
}

export function useUpdateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      workflowId,
      data,
    }: {
      workflowId: string;
      data: {
        name?: string;
        trigger_type?: string;
        trigger_config?: Record<string, unknown>;
        actions?: Record<string, unknown>[];
        status?: string;
      };
    }) => automationsApi.updateWorkflow(workflowId, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workflows'] }),
  });
}

export function useRunWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (workflowId: string) =>
      automationsApi.runWorkflow(workflowId).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflows'] });
      qc.invalidateQueries({ queryKey: ['workflow-runs'] });
    },
  });
}

export function useWorkflowRuns(limit?: number) {
  return useQuery({
    queryKey: ['workflow-runs', limit],
    queryFn: () => automationsApi.listRuns({ limit }).then((r) => r.data),
  });
}

export function useAutomationEvents(limit?: number) {
  return useQuery({
    queryKey: ['automation-events', limit],
    queryFn: () => automationsApi.listEvents({ limit }).then((r) => r.data),
  });
}
