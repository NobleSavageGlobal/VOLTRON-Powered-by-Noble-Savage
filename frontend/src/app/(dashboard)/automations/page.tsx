'use client';

import { Header } from '@/components/layout/Header';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import { Zap, Clock, CheckCircle } from 'lucide-react';

const SAMPLE_AUTOMATIONS = [
  {
    id: '1',
    name: 'Document Auto-Classification',
    description: 'Automatically classify uploaded documents using AI',
    status: 'active' as const,
    lastRun: '2 minutes ago',
    runCount: 147,
    trigger: 'On document upload',
  },
  {
    id: '2',
    name: 'Task Generation from Documents',
    description: 'Generate action tasks from processed documents',
    status: 'active' as const,
    lastRun: '1 hour ago',
    runCount: 23,
    trigger: 'When document processed',
  },
  {
    id: '3',
    name: 'Overdue Task Alerts',
    description: 'Send alerts when tasks are overdue',
    status: 'paused' as const,
    lastRun: '3 days ago',
    runCount: 8,
    trigger: 'Daily at 9:00 AM',
  },
];

export default function AutomationsPage() {
  return (
    <div className="flex flex-col flex-1">
      <Header title="Automations" subtitle="Automated workflows and rules" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        <div className="grid grid-cols-1 gap-4">
          {SAMPLE_AUTOMATIONS.map((auto) => (
            <Card key={auto.id} className="hover:border-slate-600 transition">
              <div className="flex items-start gap-4">
                <div className="p-2.5 bg-amber-500/10 rounded-xl flex-shrink-0">
                  <Zap className="w-5 h-5 text-amber-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-semibold text-slate-100">{auto.name}</h3>
                    <StatusIndicator
                      status={auto.status === 'active' ? 'online' : 'offline'}
                      label={auto.status}
                    />
                  </div>
                  <p className="text-sm text-slate-400">{auto.description}</p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      {auto.trigger}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Last run {auto.lastRun}
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      {auto.runCount} runs
                    </span>
                  </div>
                </div>
                <Badge
                  label={auto.status}
                  colorClass={auto.status === 'active'
                    ? 'text-emerald-400 bg-emerald-400/10'
                    : 'text-slate-400 bg-slate-400/10'}
                />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
