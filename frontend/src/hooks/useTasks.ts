'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '@/lib/api';
import type { PaginatedResponse, Task } from '@/lib/types';

export function useTasks(params?: {
  status?: string;
  priority?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: async () => {
      const resp = await tasksApi.list(params);
      return resp.data as PaginatedResponse<Task>;
    },
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      description?: string;
      status?: string;
      priority?: string;
      due_date?: string;
    }) => tasksApi.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { status?: string; priority?: string; title?: string };
    }) => tasksApi.update(id, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tasksApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}
