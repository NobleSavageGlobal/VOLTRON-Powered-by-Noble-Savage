'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { clientsApi } from '@/lib/api';
import type { Client } from '@/lib/types';

export function useClients(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['clients', params],
    queryFn: async () => {
      const resp = await clientsApi.list(params);
      return resp.data as Client[];
    },
  });
}

export function useClient(id: string) {
  return useQuery({
    queryKey: ['client', id],
    queryFn: async () => {
      const resp = await clientsApi.get(id);
      return resp.data as Client;
    },
    enabled: Boolean(id),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      display_name: string;
      entity_type?: string;
      industry?: string;
      annual_revenue_range?: string;
    }) => clientsApi.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients'] }),
  });
}

export function useUpdateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: {
        display_name?: string;
        entity_type?: string;
        industry?: string;
        annual_revenue_range?: string;
        status?: string;
      };
    }) => clientsApi.update(id, data).then((r) => r.data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['clients'] });
      qc.invalidateQueries({ queryKey: ['client', id] });
    },
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => clientsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients'] }),
  });
}
