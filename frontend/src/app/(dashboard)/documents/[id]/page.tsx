"use client";

import { useParams, useRouter } from "next/navigation";
import {
  useAutoOnboardDocument,
  useDocument,
  useReprocessDocument,
} from "@/hooks/useDocuments";
import { Header } from "@/components/layout/Header";
import { ExtractedDataView } from "@/components/documents/ExtractedDataView";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ArrowLeft, RefreshCw, UserPlus } from "lucide-react";
import {
  formatDateTime,
  formatFileSize,
  getDocTypeLabel,
  getStatusColor,
} from "@/lib/utils";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data: doc, isLoading } = useDocument(params.id);
  const { mutate: reprocess, isPending: isReprocessing } =
    useReprocessDocument();
  const { mutate: autoOnboard, isPending: isOnboarding } =
    useAutoOnboardDocument();

  if (isLoading) {
    return (
      <div className="flex flex-col flex-1">
        <Header title="Document" />
        <div className="flex justify-center items-center flex-1">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex flex-col flex-1">
        <Header title="Document Not Found" />
        <div className="p-6">
          <Button variant="secondary" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1">
      <Header
        title={doc.original_filename}
        subtitle={getDocTypeLabel(doc.doc_type)}
      />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => reprocess(doc.id)}
            disabled={isReprocessing}
          >
            {isReprocessing ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Reprocess
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => autoOnboard({ documentId: doc.id })}
            disabled={isOnboarding || doc.status === "processing"}
          >
            {isOnboarding ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <UserPlus className="w-4 h-4 mr-2" />
            )}
            {doc.client_id
              ? "Refresh Onboarding Data"
              : "Create Client From Document"}
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Document Info</CardTitle>
            </CardHeader>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Status</span>
                <Badge
                  label={doc.status}
                  colorClass={getStatusColor(doc.status)}
                />
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Type</span>
                <span className="text-slate-200">
                  {getDocTypeLabel(doc.doc_type)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Size</span>
                <span className="text-slate-200">
                  {formatFileSize(doc.file_size)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">MIME</span>
                <span className="text-slate-200 text-xs">{doc.mime_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Uploaded</span>
                <span className="text-slate-200">
                  {formatDateTime(doc.created_at)}
                </span>
              </div>
              {doc.processed_at && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Processed</span>
                  <span className="text-slate-200">
                    {formatDateTime(doc.processed_at)}
                  </span>
                </div>
              )}
              {doc.confidence_score !== null && (
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-400">Confidence</span>
                    <span className="text-slate-200">
                      {Math.round(doc.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-1.5">
                    <div
                      className="bg-indigo-500 h-1.5 rounded-full"
                      style={{ width: `${doc.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {doc.client_id && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Linked Client</span>
                  <span className="text-slate-200 text-xs font-mono">
                    {doc.client_id}
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Extracted Data */}
          <div className="lg:col-span-2">
            <ExtractedDataView document={doc} />
          </div>
        </div>
      </div>
    </div>
  );
}
