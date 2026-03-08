"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X, CheckCircle2, AlertCircle } from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";
import { useBatchUploadDocuments } from "@/hooks/useDocuments";
import { useClients } from "@/hooks/useClients";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import type { DocumentUploadResult } from "@/lib/types";

interface DocumentUploadProps {
  onSuccess?: () => void;
  defaultAutoOnboard?: boolean;
  lockAutoOnboard?: boolean;
}

export function DocumentUpload({
  onSuccess,
  defaultAutoOnboard = false,
  lockAutoOnboard = false,
}: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const { mutateAsync: uploadBatch, isPending } = useBatchUploadDocuments();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [results, setResults] = useState<DocumentUploadResult[]>([]);
  const [autoOnboard, setAutoOnboard] = useState(defaultAutoOnboard);
  const [selectedClientId, setSelectedClientId] = useState("");
  const { data: clients } = useClients({ status: "active", limit: 200 });

  const onDrop = useCallback((accepted: File[]) => {
    setResults([]);
    setFiles((prev) => [...prev, ...accepted.slice(0, 10 - prev.length)]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/tiff": [".tiff", ".tif"],
      "image/webp": [".webp"],
      "image/bmp": [".bmp"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
    },
    maxSize: 50 * 1024 * 1024,
    disabled: isPending,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[index];
      return next;
    });
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const newErrors: Record<string, string> = {};
    const response = await uploadBatch({
      files,
      autoOnboard,
      clientId: selectedClientId || undefined,
    });

    response.items.forEach((result, i) => {
      if (!result.success) {
        newErrors[i] = result.error || "Upload failed";
      }
    });

    setResults(response.items);
    setErrors(newErrors);

    if (response.failure_count === 0) {
      setFiles([]);
      onSuccess?.();
    }
  };

  const successCount = results.filter((item) => item.success).length;
  const failureCount = results.filter((item) => !item.success).length;

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition",
          isDragActive
            ? "border-indigo-500 bg-indigo-500/10"
            : "border-slate-600 hover:border-indigo-500/60 hover:bg-slate-800/50",
          isPending && "opacity-50 cursor-not-allowed",
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="p-3 bg-slate-800 rounded-xl">
            <Upload className="w-7 h-7 text-indigo-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">
              {isDragActive ? "Drop files here" : "Drag & drop documents"}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              PDF, images, DOC/DOCX, TXT/CSV - up to 50MB each
            </p>
          </div>
          <Button variant="secondary" size="sm" type="button">
            Browse files
          </Button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 space-y-3">
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={autoOnboard}
                disabled={lockAutoOnboard || isPending}
                onChange={(e) => setAutoOnboard(e.target.checked)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-indigo-500"
              />
              Auto-populate client onboarding from extracted document fields
            </label>

            {autoOnboard && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Attach to existing client (optional)
                </label>
                <select
                  value={selectedClientId}
                  onChange={(e) => setSelectedClientId(e.target.value)}
                  disabled={isPending}
                  className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Create client from upload data</option>
                  {(clients ?? []).map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.display_name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700"
            >
              <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate">{file.name}</p>
                <p className="text-xs text-slate-500">
                  {formatFileSize(file.size)}
                </p>
                {errors[i] && (
                  <p className="text-xs text-red-400">{errors[i]}</p>
                )}
              </div>
              {isPending ? (
                <Spinner size="sm" />
              ) : (
                <button
                  onClick={() => removeFile(i)}
                  className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}

          <Button
            onClick={handleUpload}
            disabled={isPending || files.length === 0}
            className="w-full"
          >
            {isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Uploading and extracting...
              </>
            ) : (
              `Upload ${files.length} file${files.length > 1 ? "s" : ""}`
            )}
          </Button>

          {results.length > 0 && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 space-y-3">
              <p className="text-sm font-medium text-slate-200">
                Completed: {successCount} success, {failureCount} failed
              </p>
              {failureCount > 0 && (
                <p className="text-xs text-red-400">
                  Failed files can be corrected and re-uploaded without redoing
                  successful uploads.
                </p>
              )}
              <div className="space-y-2">
                {results.map((r, i) => {
                  const d = r.document;
                  return (
                    <div
                      key={`result-${i}`}
                      className={cn(
                        "flex items-start gap-3 p-2 rounded-lg text-xs",
                        r.success
                          ? "bg-emerald-900/20 border border-emerald-800/30"
                          : "bg-red-900/20 border border-red-800/30",
                      )}
                    >
                      {r.success ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-slate-200 font-medium truncate">
                          {r.filename}
                        </p>
                        {r.success && d && (
                          <div className="flex flex-wrap items-center gap-2 mt-1">
                            <span className="text-indigo-400 font-medium">
                              {d.doc_type !== "other"
                                ? d.doc_type
                                    .replace(/_/g, " ")
                                    .replace(/\b\w/g, (c) => c.toUpperCase())
                                : "Unclassified"}
                            </span>
                            {d.confidence_score !== null && (
                              <>
                                <span className="text-slate-600">·</span>
                                <span className="text-slate-400">
                                  {Math.round(d.confidence_score * 100)}%
                                  confidence
                                </span>
                              </>
                            )}
                            {d.extracted_data?.candidate_client_name && (
                              <>
                                <span className="text-slate-600">·</span>
                                <span className="text-emerald-400">
                                  {String(
                                    d.extracted_data.candidate_client_name,
                                  )}
                                </span>
                              </>
                            )}
                          </div>
                        )}
                        {r.success && d?.ai_summary && (
                          <p className="text-slate-500 mt-1 line-clamp-1">
                            {d.ai_summary}
                          </p>
                        )}
                        {!r.success && r.error && (
                          <p className="text-red-400 mt-0.5">{r.error}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
