'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';
import { cn, formatFileSize } from '@/lib/utils';
import { useUploadDocument } from '@/hooks/useDocuments';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';

interface DocumentUploadProps {
  onSuccess?: () => void;
}

export function DocumentUpload({ onSuccess }: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const { mutateAsync: upload, isPending } = useUploadDocument();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const onDrop = useCallback(
    (accepted: File[]) => {
      setFiles((prev) => [...prev, ...accepted.slice(0, 10 - prev.length)]);
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
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
    const newErrors: Record<string, string> = {};
    const results = await Promise.allSettled(files.map((f) => upload(f)));
    results.forEach((result, i) => {
      if (result.status === 'rejected') {
        newErrors[i] = 'Upload failed';
      }
    });
    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      setFiles([]);
      onSuccess?.();
    }
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition',
          isDragActive
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-slate-600 hover:border-indigo-500/60 hover:bg-slate-800/50',
          isPending && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="p-3 bg-slate-800 rounded-xl">
            <Upload className="w-7 h-7 text-indigo-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">
              {isDragActive ? 'Drop files here' : 'Drag & drop documents'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              PDF, JPEG, PNG, TIFF, DOC, DOCX — up to 50MB each
            </p>
          </div>
          <Button variant="secondary" size="sm" type="button">
            Browse files
          </Button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700"
            >
              <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200 truncate">{file.name}</p>
                <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
                {errors[i] && <p className="text-xs text-red-400">{errors[i]}</p>}
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
                Uploading...
              </>
            ) : (
              `Upload ${files.length} file${files.length > 1 ? 's' : ''}`
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
