"use client";

import { useMemo, useState } from "react";
import { useDocuments } from "@/hooks/useDocuments";
import { Header } from "@/components/layout/Header";
import { DocumentCard } from "@/components/documents/DocumentCard";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  Clock,
  BarChart3,
} from "lucide-react";
import { getDocTypeLabel } from "@/lib/utils";

const STATUS_OPTIONS = [
  "",
  "pending",
  "processing",
  "processed",
  "failed",
  "review_required",
];
const TYPE_OPTIONS = [
  "",
  "bank_statement",
  "tax_return",
  "contract",
  "invoice",
  "credit_report",
  "government",
  "other",
];

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 p-4 bg-slate-800/50 border border-slate-700 rounded-xl">
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  const [showUpload, setShowUpload] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const { data, isLoading, refetch } = useDocuments({
    status: statusFilter || undefined,
    doc_type: typeFilter || undefined,
    page_size: 50,
  });

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    const processed = items.filter((d) => d.status === "processed").length;
    const needsReview = items.filter(
      (d) => d.status === "review_required" || d.status === "failed",
    ).length;
    const pending = items.filter(
      (d) => d.status === "pending" || d.status === "processing",
    ).length;
    const typeCounts: Record<string, number> = {};
    items.forEach((d) => {
      typeCounts[d.doc_type] = (typeCounts[d.doc_type] || 0) + 1;
    });
    const avgConfidence =
      items.length > 0
        ? items.reduce((sum, d) => sum + (d.confidence_score ?? 0), 0) /
          items.length
        : 0;
    return {
      total: data?.total ?? 0,
      processed,
      needsReview,
      pending,
      typeCounts,
      avgConfidence,
    };
  }, [data]);

  return (
    <div className="flex flex-col flex-1">
      <Header
        title="Documents"
        subtitle="Upload, analyze, and manage business documents"
      />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Stats Overview */}
        {!isLoading && stats.total > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={FileText}
              label="Total Documents"
              value={stats.total}
              color="bg-indigo-600/20 text-indigo-400"
            />
            <StatCard
              icon={CheckCircle}
              label="Processed"
              value={stats.processed}
              color="bg-emerald-600/20 text-emerald-400"
            />
            <StatCard
              icon={AlertTriangle}
              label="Needs Review"
              value={stats.needsReview}
              color="bg-amber-600/20 text-amber-400"
            />
            <StatCard
              icon={BarChart3}
              label="Avg Confidence"
              value={`${Math.round(stats.avgConfidence * 100)}%`}
              color="bg-blue-600/20 text-blue-400"
            />
          </div>
        )}

        {/* Type breakdown */}
        {!isLoading && Object.keys(stats.typeCounts).length > 1 && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.typeCounts)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <button
                  key={type}
                  onClick={() => setTypeFilter(typeFilter === type ? "" : type)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition border ${
                    typeFilter === type
                      ? "bg-indigo-600 border-indigo-500 text-white"
                      : "bg-slate-800 border-slate-700 text-slate-300 hover:border-indigo-500/50"
                  }`}
                >
                  {getDocTypeLabel(type)} ({count})
                </button>
              ))}
          </div>
        )}

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
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          {(statusFilter || typeFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setStatusFilter("");
                setTypeFilter("");
              }}
            >
              Clear filters
            </Button>
          )}
        </div>

        {/* Document List */}
        <Card padding={false} className="p-4">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : (
            <div className="space-y-2">
              {(data?.items ?? []).map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))}
              {(data?.items ?? []).length === 0 && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm font-medium">
                    No documents found
                  </p>
                  <p className="text-slate-500 text-xs mt-1">
                    Upload documents to start extracting insights
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-4"
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
        <DocumentUpload
          onSuccess={() => {
            setShowUpload(false);
            refetch();
          }}
        />
      </Modal>
    </div>
  );
}
