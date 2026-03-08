'use client';

import { orgsApi } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { Header } from '@/components/layout/Header';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { Building2, User, Shield } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const { data: org, isLoading: orgLoading } = useQuery({
    queryKey: ['org-me'],
    queryFn: () => orgsApi.getMe().then((r) => r.data),
    enabled: Boolean(user?.org_id),
    retry: false,
  });

  return (
    <div className="flex flex-col flex-1">
      <Header title="Settings" subtitle="Manage your account and organization" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto max-w-2xl">
        {/* Profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-indigo-400" />
              <CardTitle>Profile</CardTitle>
            </div>
          </CardHeader>
          {user && (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Full name</span>
                <span className="text-slate-200">{user.full_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Email</span>
                <span className="text-slate-200">{user.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Role</span>
                <Badge label={user.role} colorClass="text-indigo-400 bg-indigo-400/10" />
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status</span>
                <Badge
                  label={user.is_active ? 'Active' : 'Inactive'}
                  colorClass={user.is_active ? 'text-emerald-400 bg-emerald-400/10' : 'text-red-400 bg-red-400/10'}
                />
              </div>
            </div>
          )}
        </Card>

        {/* Organization */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <CardTitle>Organization</CardTitle>
            </div>
          </CardHeader>
          {orgLoading ? (
            <div className="flex justify-center py-4"><Spinner /></div>
          ) : org ? (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Name</span>
                <span className="text-slate-200">{org.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Slug</span>
                <span className="text-slate-200 font-mono">{org.slug}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Plan</span>
                <Badge label={org.plan} colorClass="text-amber-400 bg-amber-400/10" />
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No organization linked to your account.</p>
          )}
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-400" />
              <CardTitle>Security</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-slate-200">Two-Factor Authentication</p>
                <p className="text-xs text-slate-500">Add an extra layer of security</p>
              </div>
              <Badge label="Coming soon" colorClass="text-slate-400 bg-slate-400/10" />
            </div>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-slate-200">API Keys</p>
                <p className="text-xs text-slate-500">Manage API access tokens</p>
              </div>
              <Badge label="Coming soon" colorClass="text-slate-400 bg-slate-400/10" />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
