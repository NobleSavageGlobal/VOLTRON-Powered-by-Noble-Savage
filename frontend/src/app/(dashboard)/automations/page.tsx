'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Spinner } from '@/components/ui/Spinner';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import {
  useWorkflows,
  useCreateWorkflow,
  useUpdateWorkflow,
  useRunWorkflow,
  useWorkflowRuns,
} from '@/hooks/useAutomations';
import { Zap, Clock, CheckCircle, Plus, Play, Pause, Power } from 'lucide-react';
import { timeAgo } from '@/lib/utils';
import type { Workflow } from '@/lib/types';

const TRIGGER_TYPES = [
  { value: 'document_uploaded', label: 'On document upload' },
  { value: 'document_processed', label: 'When document processed' },
  { value: 'task_created', label: 'When task created' },
  { value: 'client_created', label: 'When client created' },
  { value: 'schedule', label: 'On schedule' },
];

function WorkflowCard({
  workflow,
  onToggle,
  onRun,
}: {
  workflow: Workflow;
  onToggle: (w: Workflow) => void;
  onRun: (id: string) => void;
}) {
  const isActive = workflow.status === 'active';
  return (
    <Card className="hover:border-slate-600 transition">
      <div className="flex items-start gap-4">
        <div className="p-2.5 bg-amber-500/10 rounded-xl flex-shrink-0">
          <Zap className="w-5 h-5 text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="font-semibold text-slate-100">{workflow.name}</h3>
            <StatusIndicator
              status={isActive ? 'online' : 'offline'}
              label={workflow.status}
            />
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {TRIGGER_TYPES.find((t) => t.value === workflow.trigger_type)?.label ??
                workflow.trigger_type}
            </span>
            {workflow.last_triggered_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {timeAgo(workflow.last_triggered_at)}
              </span>
            )}
            <span className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {workflow.run_count} runs
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => onRun(workflow.id)}
            className="p-1.5 rounded text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10 transition"
            title="Run now"
          >
            <Play className="w-4 h-4" />
          </button>
          <button
            onClick={() => onToggle(workflow)}
            className="p-1.5 rounded text-slate-400 hover:text-amber-400 hover:bg-amber-400/10 transition"
            title={isActive ? 'Pause' : 'Activate'}
          >
            {isActive ? <Pause className="w-4 h-4" /> : <Power className="w-4 h-4" />}
          </button>
          <Badge
            label={workflow.status}
            colorClass={
              isActive
                ? 'text-emerald-400 bg-emerald-400/10'
                : 'text-slate-400 bg-slate-400/10'
            }
          />
        </div>
      </div>
    </Card>
  );
}

export default function AutomationsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [triggerType, setTriggerType] = useState(TRIGGER_TYPES[0].value);

  const { data: workflows, isLoading } = useWorkflows();
  const { data: runs } = useWorkflowRuns(5);
  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const runWorkflow = useRunWorkflow();

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createWorkflow.mutateAsync({
      name: name.trim(),
      trigger_type: triggerType,
      trigger_config: {},
      actions: [],
    });
    setName('');
    setShowCreate(false);
  };

  const handleToggle = (w: Workflow) => {
    updateWorkflow.mutate({
      workflowId: w.id,
      data: { status: w.status === 'active' ? 'paused' : 'active' },
    });
  };

  const activeCount = workflows?.filter((w: Workflow) => w.status === 'active').length ?? 0;

  return (
    <div className="flex flex-col flex-1">
      <Header title="Automations" subtitle="Automated workflows and rules" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <span className="text-sm text-slate-400">
            {workflows
              ? `${activeCount} active workflow${activeCount !== 1 ? 's' : ''} of ${workflows.length}`
              : ''}
          </span>
          <Button onClick={() => setShowCreate(true)} size="sm">
            <Plus className="w-4 h-4 mr-1.5" />
            New Workflow
          </Button>
        </div>

        {/* Workflows list */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : !workflows || workflows.length === 0 ? (
          <Card className="p-12 text-center">
            <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <div className="text-slate-400 font-medium">No workflows yet</div>
            <div className="text-slate-600 text-sm mt-1">
              Create your first automation to streamline repetitive tasks.
            </div>
            <Button onClick={() => setShowCreate(true)} size="sm" className="mt-4">
              <Plus className="w-4 h-4 mr-1.5" />
              Create First Workflow
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {workflows.map((w: Workflow) => (
              <WorkflowCard
                key={w.id}
                workflow={w}
                onToggle={handleToggle}
                onRun={(id) => runWorkflow.mutate(id)}
              />
            ))}
          </div>
        )}

        {/* Recent runs */}
        {runs && runs.length > 0 && (
          <Card>
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Recent Runs</h3>
            <div className="space-y-2">
              {runs.map((run: { id: string; status: string; started_at: string }) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between text-xs text-slate-400 py-1.5 border-b border-slate-800 last:border-0"
                >
                  <Badge
                    label={run.status}
                    colorClass={
                      run.status === 'completed'
                        ? 'text-emerald-400 bg-emerald-400/10'
                        : run.status === 'failed'
                        ? 'text-red-400 bg-red-400/10'
                        : 'text-blue-400 bg-blue-400/10'
                    }
                  />
                  <span>{timeAgo(run.started_at)}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="New Workflow">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Workflow Name
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Auto-classify uploads"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Trigger</label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {TRIGGER_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createWorkflow.isPending || !name.trim()}
            >
              {createWorkflow.isPending ? 'Creating...' : 'Create Workflow'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
