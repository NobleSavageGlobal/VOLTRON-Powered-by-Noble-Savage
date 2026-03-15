'use client';

import { useDocuments } from '@/hooks/useDocuments';
import { useTasks } from '@/hooks/useTasks';
import { Header } from '@/components/layout/Header';
import { StatsCard } from '@/components/dashboard/StatsCard';

import { QuickActions } from '@/components/dashboard/QuickActions';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { FileText, CheckSquare, TrendingUp, AlertCircle } from 'lucide-react';
import { formatDate, getDocTypeLabel, getStatusColor, getPriorityColor } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: docsData, isLoading: docsLoading } = useDocuments({ page_size: 5 });
  const { data: tasksData, isLoading: tasksLoading } = useTasks({ page_size: 5 });
  const { data: criticalTasks } = useTasks({ priority: 'critical', status: 'todo' });
  const { data: processedDocs } = useDocuments({ status: 'processed' });

  const totalDocs = docsData?.total ?? 0;
  const totalTasks = tasksData?.total ?? 0;
  const processedCount = processedDocs?.total ?? 0;
  const criticalCount = criticalTasks?.total ?? 0;
  const readiness = totalDocs > 0 ? Math.round((processedCount / totalDocs) * 100) : 0;

  return (
    <div className="flex flex-col flex-1">
      <Header title="Command Center" subtitle="BBA Services Entrepreneur OS" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Total Documents"
            value={totalDocs}
            subtitle={`${processedCount} processed`}
            icon={<FileText className="w-5 h-5" />}
          />
          <StatsCard
            title="Open Tasks"
            value={totalTasks}
            subtitle={`${criticalCount} critical`}
            icon={<CheckSquare className="w-5 h-5" />}
            trend={criticalCount > 0 ? 'down' : 'neutral'}
            trendValue={criticalCount > 0 ? `${criticalCount} need attention` : 'All on track'}
          />
          <StatsCard
            title="Readiness Score"
            value={`${readiness}%`}
            subtitle="Documents processed"
            icon={<TrendingUp className="w-5 h-5" />}
            trend={readiness > 70 ? 'up' : 'neutral'}
          />
          <StatsCard
            title="Critical Items"
            value={criticalCount}
            subtitle="Require immediate action"
            icon={<AlertCircle className="w-5 h-5" />}
            trend={criticalCount > 0 ? 'down' : 'up'}
            trendValue={criticalCount === 0 ? 'All clear' : undefined}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <QuickActions />
          </Card>

          {/* Recent Documents */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex items-center justify-between">
              <CardTitle>Recent Documents</CardTitle>
              <Link href="/documents" className="text-xs text-indigo-400 hover:text-indigo-300">
                View all
              </Link>
            </CardHeader>
            {docsLoading ? (
              <div className="flex justify-center py-6">
                <Spinner />
              </div>
            ) : (
              <div className="space-y-2">
                {(docsData?.items ?? []).map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/documents/${doc.id}`}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">
                        {doc.original_filename}
                      </p>
                      <p className="text-xs text-slate-500">{getDocTypeLabel(doc.doc_type)}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge label={doc.status} colorClass={getStatusColor(doc.status)} />
                      <span className="text-xs text-slate-500">{formatDate(doc.created_at)}</span>
                    </div>
                  </Link>
                ))}
                {(docsData?.items ?? []).length === 0 && (
                  <p className="text-sm text-slate-500 py-4 text-center">No documents yet</p>
                )}
              </div>
            )}
          </Card>
        </div>

        {/* Tasks */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Upcoming Tasks</CardTitle>
            <Link href="/tasks" className="text-xs text-indigo-400 hover:text-indigo-300">
              View all
            </Link>
          </CardHeader>
          {tasksLoading ? (
            <div className="flex justify-center py-6"><Spinner /></div>
          ) : (
            <div className="space-y-2">
              {(tasksData?.items ?? []).map((task) => (
                <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200">{task.title}</p>
                    {task.description && (
                      <p className="text-xs text-slate-500 truncate">{task.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge label={task.priority} colorClass={getPriorityColor(task.priority)} />
                    <Badge label={task.status} colorClass={getStatusColor(task.status)} />
                  </div>
                </div>
              ))}
              {(tasksData?.items ?? []).length === 0 && (
                <p className="text-sm text-slate-500 py-4 text-center">No tasks yet</p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
