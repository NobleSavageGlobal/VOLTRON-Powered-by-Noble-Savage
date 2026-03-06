'use client';

import { useState } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import { Header } from '@/components/layout/Header';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { DocumentUpload } from '@/components/documents/DocumentUpload';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Spinner } from '@/components/ui/Spinner';
import { Upload } from 'lucide-react';

const STATUS_OPTIONS = ['', 'pending', 'processing', 'processed', 'failed', 'review_required'];
const TYPE_OPTIONS = ['', 'bank_statement', 'tax_return', 'contract', 'invoice', 'credit_report', 'government', 'other'];

export default function DocumentsPage() {
  const [showUpload, setShowUpload] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading, refetch } = useDocuments({
    status: statusFilter || undefined,
    doc_type: typeFilter || undefined,
    page_size: 50,
  });

  return (
    <div className="flex flex-col flex-1">
      <Header title="Documents" subtitle="Upload and manage business documents" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setShowUpload(true)}>
            <Upload className="w-4 h-4 mr-2" />
            Upload Documents
          </Button>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.slice(1).map((s) => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All types</option>
            {TYPE_OPTIONS.slice(1).map((t) => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        {/* Document List */}
        <Card padding={false} className="p-4">
          {isLoading ? (
            <div className="flex justify-center py-12"><Spinner size="lg" /></div>
          ) : (
            <div className="space-y-2">
              {(data?.items ?? []).map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))}
              {(data?.items ?? []).length === 0 && (
                <div className="text-center py-12">
                  <p className="text-slate-500 text-sm">No documents found</p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-3"
                    onClick={() => setShowUpload(true)}
                  >
                    Upload your first document
                  </Button>
                </div>
              )}
            </div>
          )}
          {data && data.total > 0 && (
            <p className="mt-4 text-xs text-slate-500 text-center">
              Showing {data.items.length} of {data.total} documents
            </p>
          )}
        </Card>
      </div>

      <Modal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Documents"
      >
        <DocumentUpload onSuccess={() => { setShowUpload(false); refetch(); }} />
      </Modal>
    </div>
  );
}
