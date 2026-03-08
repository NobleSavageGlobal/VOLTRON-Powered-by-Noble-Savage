import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export function StatsCard({ title, value, subtitle, icon, trend, trendValue }: StatsCardProps) {
  return (
    <Card className="flex items-start gap-4">
      <div className="p-2.5 bg-indigo-600/20 rounded-xl text-indigo-400 flex-shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-slate-50 mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        {trendValue && (
          <p
            className={cn(
              'text-xs mt-1',
              trend === 'up' && 'text-emerald-400',
              trend === 'down' && 'text-red-400',
              trend === 'neutral' && 'text-slate-400'
            )}
          >
            {trendValue}
          </p>
        )}
      </div>
    </Card>
  );
}
