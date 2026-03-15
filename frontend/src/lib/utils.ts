import { clsx, type ClassValue } from 'clsx';
import { format, formatDistanceToNow } from 'date-fns';

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy');
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy HH:mm');
}

export function timeAgo(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

export function getDocTypeLabel(docType: string): string {
  const labels: Record<string, string> = {
    bank_statement: 'Bank Statement',
    tax_return: 'Tax Return',
    contract: 'Contract',
    invoice: 'Invoice',
    credit_report: 'Credit Report',
    government: 'Government ID',
    other: 'Other',
  };
  return labels[docType] ?? capitalize(docType);
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-amber-400 bg-amber-400/10',
    processing: 'text-blue-400 bg-blue-400/10',
    processed: 'text-emerald-400 bg-emerald-400/10',
    failed: 'text-red-400 bg-red-400/10',
    review_required: 'text-orange-400 bg-orange-400/10',
    todo: 'text-slate-400 bg-slate-400/10',
    in_progress: 'text-blue-400 bg-blue-400/10',
    blocked: 'text-red-400 bg-red-400/10',
    review: 'text-amber-400 bg-amber-400/10',
    done: 'text-emerald-400 bg-emerald-400/10',
  };
  return colors[status] ?? 'text-slate-400 bg-slate-400/10';
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-400 bg-red-400/10',
    high: 'text-orange-400 bg-orange-400/10',
    medium: 'text-amber-400 bg-amber-400/10',
    low: 'text-slate-400 bg-slate-400/10',
  };
  return colors[priority] ?? 'text-slate-400 bg-slate-400/10';
}
