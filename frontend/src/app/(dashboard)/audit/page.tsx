'use client';

import { auditApi } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { formatDateTime } from '@/lib/utils';
import { Shield } from 'lucide-react';

export default function AuditPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: () => auditApi.list({ page_size: 100 }).then((r) => r.data),
  });

  return (
    <div className="flex flex-col flex-1">
      <Header title="Audit Log" subtitle="All system activity" />
      <div className="flex-1 p-6 overflow-y-auto">
        <Card padding={false}>
          {isLoading ? (
            <div className="flex justify-center py-12"><Spinner size="lg" /></div>
          ) : (
            <div className="divide-y divide-slate-800">
              {(data?.items ?? []).length === 0 && (
                <div className="flex flex-col items-center py-12 text-slate-500">
                  <Shield className="w-8 h-8 mb-2 opacity-40" />
                  <p className="text-sm">No audit events yet</p>
                </div>
              )}
              {(data?.items ?? []).map((entry) => (
                <div key={entry.id} className="flex items-start gap-4 px-6 py-4 hover:bg-slate-800/40 transition">
                  <div className="w-2 h-2 mt-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-200 capitalize">
                        {entry.action.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-slate-500 capitalize">{entry.resource_type}</span>
                      {entry.resource_id && (
                        <span className="text-xs text-slate-600 font-mono truncate max-w-xs">
                          {entry.resource_id}
                        </span>
                      )}
                    </div>
                    {entry.ip_address && (
                      <p className="text-xs text-slate-500 mt-0.5">IP: {entry.ip_address}</p>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 flex-shrink-0">
                    {formatDateTime(entry.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
