'use client';

import { timeAgo } from '@/lib/utils';

interface ActivityItem {
  id: string;
  action: string;
  resource_type: string;
  timestamp: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500 py-4 text-center">No recent activity</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-3">
          <div className="w-2 h-2 mt-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-slate-300">
              <span className="font-medium capitalize">{item.action.replace(/_/g, ' ')}</span>
              {' — '}
              <span className="text-slate-400 capitalize">{item.resource_type}</span>
            </p>
            <p className="text-xs text-slate-500">{timeAgo(item.timestamp)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
