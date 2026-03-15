import { cn } from '@/lib/utils';

interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'warning' | 'error';
  label?: string;
  className?: string;
}

const statusClasses: Record<string, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
};

export function StatusIndicator({ status, label, className }: StatusIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className={cn('w-2 h-2 rounded-full', statusClasses[status])} />
      {label && <span className="text-sm text-slate-400">{label}</span>}
    </div>
  );
}
