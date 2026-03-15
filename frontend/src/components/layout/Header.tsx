'use client';

import { Bell } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="h-16 border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm px-6 flex items-center justify-between flex-shrink-0">
      <div>
        <h1 className="text-lg font-semibold text-slate-50">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition">
          <Bell className="w-5 h-5" />
        </button>
        {user && (
          <div className="w-8 h-8 rounded-full bg-indigo-700 flex items-center justify-center text-sm font-bold text-white">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
}
