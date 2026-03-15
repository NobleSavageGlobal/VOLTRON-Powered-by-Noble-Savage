import { cn, capitalize } from '@/lib/utils';

interface BadgeProps {
  label: string;
  className?: string;
  colorClass?: string;
}

export function Badge({ label, className, colorClass }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium',
        colorClass ?? 'bg-slate-700 text-slate-300',
        className
      )}
    >
      {capitalize(label)}
    </span>
  );
}
