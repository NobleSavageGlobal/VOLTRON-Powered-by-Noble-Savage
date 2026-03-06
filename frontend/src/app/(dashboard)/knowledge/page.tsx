'use client';

import { Header } from '@/components/layout/Header';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { useDocuments } from '@/hooks/useDocuments';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { Search, Database } from 'lucide-react';
import { Spinner } from '@/components/ui/Spinner';
import { useState } from 'react';

export default function KnowledgePage() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useDocuments({ status: 'processed', page_size: 50 });

  const filtered = (data?.items ?? []).filter(
    (d) =>
      !search ||
      d.original_filename.toLowerCase().includes(search.toLowerCase()) ||
      d.ai_summary?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col flex-1">
      <Header title="Knowledge Vault" subtitle="Insights extracted from your documents" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents, summaries, and insights..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <CardTitle>Processed Documents</CardTitle>
            </div>
          </CardHeader>
          {isLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <div className="space-y-2">
              {filtered.map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))}
              {filtered.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-6">
                  {search ? 'No documents match your search' : 'No processed documents yet'}
                </p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
