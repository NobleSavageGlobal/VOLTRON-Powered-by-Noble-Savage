'use client';

import Link from 'next/link';
import { FileUp, Plus, RefreshCw } from 'lucide-react';

const actions = [
  { href: '/documents', label: 'Upload Document', icon: FileUp, color: 'indigo' },
  { href: '/tasks', label: 'New Task', icon: Plus, color: 'emerald' },
  { href: '/automations', label: 'Automations', icon: RefreshCw, color: 'amber' },
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-3 gap-3">
      {actions.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className="flex flex-col items-center gap-2 p-4 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition text-center group"
        >
          <div className="p-2 bg-indigo-600/20 rounded-lg group-hover:bg-indigo-600/30 transition">
            <Icon className="w-5 h-5 text-indigo-400" />
          </div>
          <span className="text-xs font-medium text-slate-300 group-hover:text-slate-100 transition">
            {label}
          </span>
        </Link>
      ))}
    </div>
  );
}
