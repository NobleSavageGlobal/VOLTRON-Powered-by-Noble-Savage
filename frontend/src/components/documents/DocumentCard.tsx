"use client";

import Link from "next/link";
import {
  FileText,
  RefreshCw,
  Trash2,
  Landmark,
  Receipt,
  FileSignature,
  CreditCard,
  ShieldCheck,
  Building2,
  User,
  DollarSign,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  formatDate,
  formatFileSize,
  getDocTypeLabel,
  getStatusColor,
} from "@/lib/utils";
import { useDeleteDocument, useReprocessDocument } from "@/hooks/useDocuments";
import type { Document } from "@/lib/types";

const DOC_TYPE_ICON: Record<string, { icon: typeof FileText; color: string }> =
  {
    bank_statement: { icon: Landmark, color: "text-blue-400 bg-blue-600/20" },
    tax_return: { icon: Receipt, color: "text-amber-400 bg-amber-600/20" },
    contract: {
      icon: FileSignature,
      color: "text-purple-400 bg-purple-600/20",
    },
    invoice: { icon: DollarSign, color: "text-emerald-400 bg-emerald-600/20" },
    credit_report: {
      icon: CreditCard,
      color: "text-rose-400 bg-rose-600/20",
    },
    government: {
      icon: ShieldCheck,
      color: "text-cyan-400 bg-cyan-600/20",
    },
    financial_statement: {
      icon: Landmark,
      color: "text-teal-400 bg-teal-600/20",
    },
    identification: { icon: User, color: "text-orange-400 bg-orange-600/20" },
    corporate: {
      icon: Building2,
      color: "text-indigo-400 bg-indigo-600/20",
    },
  };

function getConfidenceColor(score: number): string {
  if (score >= 0.8) return "bg-emerald-500";
  if (score >= 0.5) return "bg-amber-500";
  return "bg-red-500";
}

interface DocumentCardProps {
  document: Document;
}

export function DocumentCard({ document: doc }: DocumentCardProps) {
  const { mutate: deleteDoc, isPending: isDeleting } = useDeleteDocument();
  const { mutate: reprocess, isPending: isReprocessing } =
    useReprocessDocument();

  const typeInfo = DOC_TYPE_ICON[doc.doc_type] ?? {
    icon: FileText,
    color: "text-indigo-400 bg-indigo-600/20",
  };
  const Icon = typeInfo.icon;
  const [iconText, iconBg] = typeInfo.color.split(" ");
  const confPct =
    doc.confidence_score !== null
      ? Math.round(doc.confidence_score * 100)
      : null;
  const entityName =
    (doc.extracted_data?.candidate_client_name as string) || null;
  const summarySnippet = doc.ai_summary
    ? doc.ai_summary.length > 120
      ? doc.ai_summary.slice(0, 120) + "…"
      : doc.ai_summary
    : null;

  return (
    <Link
      href={`/documents/${doc.id}`}
      className="block p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:bg-slate-800 hover:border-slate-600 transition group"
    >
      <div className="flex items-start gap-4">
        {/* Doc type icon */}
        <div className={`p-2.5 rounded-lg flex-shrink-0 ${iconBg}`}>
          <Icon className={`w-5 h-5 ${iconText}`} />
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-slate-200 truncate group-hover:text-indigo-400 transition">
              {doc.original_filename}
            </p>
            <Badge label={doc.status} colorClass={getStatusColor(doc.status)} />
          </div>

          {/* Metadata row */}
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs font-medium text-indigo-400">
              {getDocTypeLabel(doc.doc_type)}
            </span>
            <span className="text-slate-600">·</span>
            <span className="text-xs text-slate-500">
              {formatFileSize(doc.file_size)}
            </span>
            <span className="text-slate-600">·</span>
            <span className="text-xs text-slate-500">
              {formatDate(doc.created_at)}
            </span>
            {entityName && (
              <>
                <span className="text-slate-600">·</span>
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {entityName}
                </span>
              </>
            )}
            {doc.client_id && (
              <>
                <span className="text-slate-600">·</span>
                <span className="text-xs text-emerald-400">Client linked</span>
              </>
            )}
          </div>

          {/* AI Summary snippet */}
          {summarySnippet && (
            <p className="text-xs text-slate-400 mt-2 line-clamp-2">
              {summarySnippet}
            </p>
          )}
        </div>

        {/* Right side: confidence + actions */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {confPct !== null && (
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${getConfidenceColor(doc.confidence_score!)}`}
                  style={{ width: `${confPct}%` }}
                />
              </div>
              <span className="text-xs text-slate-400 w-8 text-right">
                {confPct}%
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.preventDefault();
              reprocess(doc.id);
            }}
            disabled={isReprocessing}
            aria-label="Reprocess"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.preventDefault();
              deleteDoc(doc.id);
            }}
            disabled={isDeleting}
            aria-label="Delete"
            className="hover:text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </Link>
  );
}
