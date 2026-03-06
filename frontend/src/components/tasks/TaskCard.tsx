import { getPriorityColor, getStatusColor } from '@/lib/utils';
import type { Task } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { formatDate } from '@/lib/utils';
import { Calendar, Bot, User, Zap } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  onStatusChange?: (id: string, status: string) => void;
}

const sourceIcons: Record<string, React.ReactNode> = {
  manual: <User className="w-3 h-3" />,
  ai_generated: <Bot className="w-3 h-3" />,
  automation: <Zap className="w-3 h-3" />,
};

export function TaskCard({ task, onStatusChange }: TaskCardProps) {
  return (
    <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:bg-slate-800 transition">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200">{task.title}</p>
          {task.description && (
            <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{task.description}</p>
          )}
        </div>
        <Badge label={task.priority} colorClass={getPriorityColor(task.priority)} />
      </div>

      <div className="flex items-center gap-3 mt-3">
        <Badge label={task.status.replace(/_/g, ' ')} colorClass={getStatusColor(task.status)} />
        <span className="flex items-center gap-1 text-xs text-slate-500">
          {sourceIcons[task.source]}
          {task.source.replace(/_/g, ' ')}
        </span>
        {task.due_date && (
          <span className="flex items-center gap-1 text-xs text-slate-500">
            <Calendar className="w-3 h-3" />
            {formatDate(task.due_date)}
          </span>
        )}
        {onStatusChange && task.status !== 'done' && (
          <button
            onClick={() => onStatusChange(task.id, 'done')}
            className="ml-auto text-xs text-emerald-400 hover:text-emerald-300 transition"
          >
            Mark done
          </button>
        )}
      </div>
    </div>
  );
}
