'use client';

import Link from 'next/link';
import { FileText, RefreshCw, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatDate, formatFileSize, getDocTypeLabel, getStatusColor } from '@/lib/utils';
import { useDeleteDocument, useReprocessDocument } from '@/hooks/useDocuments';
import type { Document } from '@/lib/types';

interface DocumentCardProps {
  document: Document;
}

export function DocumentCard({ document: doc }: DocumentCardProps) {
  const { mutate: deleteDoc, isPending: isDeleting } = useDeleteDocument();
  const { mutate: reprocess, isPending: isReprocessing } = useReprocessDocument();

  return (
    <div className="flex items-center gap-4 p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:bg-slate-800 transition">
      <div className="p-2.5 bg-indigo-600/20 rounded-lg flex-shrink-0">
        <FileText className="w-5 h-5 text-indigo-400" />
      </div>

      <div className="flex-1 min-w-0">
        <Link href={`/documents/${doc.id}`} className="hover:text-indigo-400 transition">
          <p className="text-sm font-medium text-slate-200 truncate">{doc.original_filename}</p>
        </Link>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-slate-500">{getDocTypeLabel(doc.doc_type)}</span>
          <span className="text-slate-600">·</span>
          <span className="text-xs text-slate-500">{formatFileSize(doc.file_size)}</span>
          <span className="text-slate-600">·</span>
          <span className="text-xs text-slate-500">{formatDate(doc.created_at)}</span>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        {doc.confidence_score !== null && (
          <span className="text-xs text-slate-400">
            {Math.round(doc.confidence_score * 100)}% conf.
          </span>
        )}
        <Badge label={doc.status} colorClass={getStatusColor(doc.status)} />
        <Button
          variant="ghost"
          size="sm"
          onClick={() => reprocess(doc.id)}
          disabled={isReprocessing}
          aria-label="Reprocess"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => deleteDoc(doc.id)}
          disabled={isDeleting}
          aria-label="Delete"
          className="hover:text-red-400"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
}
