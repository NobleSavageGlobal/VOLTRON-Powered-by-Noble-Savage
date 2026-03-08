"use client";

import {
  Calendar,
  AlertTriangle,
  Lightbulb,
  Database,
  DollarSign,
  User,
  Building2,
  Mail,
  Phone,
  MapPin,
  FileSearch,
  Shield,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { Document } from "@/lib/types";

interface ExtractedDataViewProps {
  document: Document;
}

const FIELD_LABELS: Record<string, string> = {
  candidate_client_name: "Client / Entity Name",
  entity_type: "Entity Type",
  contact_email: "Email",
  contact_phone: "Phone",
  ein: "EIN",
  ssn_last4: "SSN (last 4)",
  annual_revenue_range: "Revenue Range",
  industry: "Industry",
  address: "Address",
};

const INTERNAL_KEYS = new Set([
  "_extraction",
  "_analysis_error",
  "onboarding_hint",
  "onboarding",
  "monetary_values",
]);

function formatMonetary(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(value);
}

function FieldIcon({ fieldKey }: { fieldKey: string }) {
  switch (fieldKey) {
    case "candidate_client_name":
      return <User className="w-3.5 h-3.5 text-indigo-400" />;
    case "entity_type":
      return <Building2 className="w-3.5 h-3.5 text-blue-400" />;
    case "contact_email":
      return <Mail className="w-3.5 h-3.5 text-cyan-400" />;
    case "contact_phone":
      return <Phone className="w-3.5 h-3.5 text-cyan-400" />;
    case "address":
      return <MapPin className="w-3.5 h-3.5 text-rose-400" />;
    case "industry":
      return <Building2 className="w-3.5 h-3.5 text-violet-400" />;
    case "ein":
    case "ssn_last4":
      return <Shield className="w-3.5 h-3.5 text-amber-400" />;
    default:
      return <Database className="w-3.5 h-3.5 text-slate-500" />;
  }
}

export function ExtractedDataView({ document: doc }: ExtractedDataViewProps) {
  const data = doc.extracted_data ?? {};
  const monetaryValues =
    data.monetary_values && typeof data.monetary_values === "object"
      ? (data.monetary_values as Record<string, number>)
      : null;
  const onboardingHint =
    data.onboarding_hint && typeof data.onboarding_hint === "object"
      ? (data.onboarding_hint as Record<string, unknown>)
      : null;
  const onboarding =
    data.onboarding && typeof data.onboarding === "object"
      ? (data.onboarding as Record<string, unknown>)
      : null;
  const extraction =
    data._extraction && typeof data._extraction === "object"
      ? (data._extraction as Record<string, unknown>)
      : null;

  const displayFields = Object.entries(data).filter(
    ([key]) => !INTERNAL_KEYS.has(key) && typeof data[key] !== "object"
  );

  return (
    <div className="space-y-4">
      {/* Document Analysis */}
      {doc.ai_summary && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileSearch className="w-4 h-4 text-indigo-400" />
              <CardTitle>Document Analysis</CardTitle>
            </div>
          </CardHeader>
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
            {doc.ai_summary}
          </p>
          {extraction && (
            <div className="mt-3 pt-3 border-t border-slate-700/50 flex flex-wrap gap-3 text-xs text-slate-500">
              {extraction.methods && (
                <span>
                  Extraction: {(extraction.methods as string[]).join(", ")}
                </span>
              )}
              {typeof extraction.text_length === "number" && (
                <span>
                  {extraction.text_length.toLocaleString()} chars extracted
                </span>
              )}
              {extraction.looks_low_quality && (
                <Badge
                  label="Low quality text"
                  colorClass="text-amber-400 bg-amber-400/10"
                />
              )}
            </div>
          )}
        </Card>
      )}

      {/* Extracted Information */}
      {displayFields.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <CardTitle>Extracted Information</CardTitle>
            </div>
          </CardHeader>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            {displayFields.map(([key, val]) => (
              <div key={key} className="flex items-start gap-2.5 py-1">
                <FieldIcon fieldKey={key} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-500 mb-0.5">
                    {FIELD_LABELS[key] ??
                      key
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </p>
                  <p className="text-sm text-slate-200 break-words">
                    {String(val)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Financial Values */}
      {monetaryValues && Object.keys(monetaryValues).length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <CardTitle>Financial Values</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-2">
            {Object.entries(monetaryValues).map(([label, amount]) => (
              <div
                key={label}
                className="flex items-center justify-between py-1.5 border-b border-slate-700/40 last:border-0"
              >
                <span className="text-sm text-slate-400 capitalize">
                  {label.replace(/_/g, " ")}
                </span>
                <span className="text-sm font-medium text-emerald-300 font-mono">
                  {formatMonetary(amount)}
                </span>
              </div>
            ))}
            {Object.keys(monetaryValues).length > 1 && (
              <div className="flex items-center justify-between pt-2 border-t border-slate-600">
                <span className="text-sm font-medium text-slate-300">
                  Sum of Values
                </span>
                <span className="text-sm font-bold text-emerald-200 font-mono">
                  {formatMonetary(
                    Object.values(monetaryValues).reduce((a, b) => a + b, 0)
                  )}
                </span>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Key Dates */}
      {doc.key_dates && doc.key_dates.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-400" />
              <CardTitle>Key Dates</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-2">
            {doc.key_dates.map((kd, i) => (
              <div
                key={i}
                className="flex items-start gap-3 text-sm py-1 border-b border-slate-700/40 last:border-0"
              >
                <span className="font-mono text-indigo-300 flex-shrink-0 bg-indigo-500/10 px-2 py-0.5 rounded">
                  {kd.date}
                </span>
                <span className="text-slate-300">{kd.description}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Risks & Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {doc.risks && doc.risks.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <CardTitle>Risks & Flags</CardTitle>
              </div>
            </CardHeader>
            <ul className="space-y-2">
              {doc.risks.map((risk, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-slate-300"
                >
                  <span className="w-1.5 h-1.5 mt-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                  {risk}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {doc.opportunities && doc.opportunities.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-emerald-400" />
                <CardTitle>Opportunities</CardTitle>
              </div>
            </CardHeader>
            <ul className="space-y-2">
              {doc.opportunities.map((opp, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-slate-300"
                >
                  <span className="w-1.5 h-1.5 mt-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                  {opp}
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      {/* Onboarding Status */}
      {onboarding && (
        <Card>
          <CardHeader>
            <CardTitle>Client Onboarding</CardTitle>
          </CardHeader>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Badge
                label={
                  onboarding.auto_onboarded ? "Auto-onboarded" : "Not onboarded"
                }
                colorClass={
                  onboarding.auto_onboarded
                    ? "text-emerald-400 bg-emerald-400/10"
                    : "text-slate-400 bg-slate-400/10"
                }
              />
            </div>
            {onboarding.client_name && (
              <div className="flex gap-3">
                <span className="text-slate-400 w-28">Client</span>
                <span className="text-slate-200">
                  {String(onboarding.client_name)}
                </span>
              </div>
            )}
            {onboarding.error && (
              <p className="text-xs text-red-400 mt-1">
                {String(onboarding.error)}
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Onboarding Preview */}
      {onboardingHint && !onboarding && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-violet-400" />
              <CardTitle>Client Onboarding Preview</CardTitle>
            </div>
          </CardHeader>
          <p className="text-xs text-slate-500 mb-3">
            These fields were auto-detected and will be used if you create a
            client from this document.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {onboardingHint.display_name && (
              <div>
                <p className="text-xs text-slate-500">Name</p>
                <p className="text-slate-200">
                  {String(onboardingHint.display_name)}
                </p>
              </div>
            )}
            {onboardingHint.entity_type && (
              <div>
                <p className="text-xs text-slate-500">Entity Type</p>
                <p className="text-slate-200 capitalize">
                  {String(onboardingHint.entity_type)}
                </p>
              </div>
            )}
            {onboardingHint.industry && (
              <div>
                <p className="text-xs text-slate-500">Industry</p>
                <p className="text-slate-200">
                  {String(onboardingHint.industry)}
                </p>
              </div>
            )}
            {onboardingHint.annual_revenue_range && (
              <div>
                <p className="text-xs text-slate-500">Revenue Range</p>
                <p className="text-slate-200">
                  {String(onboardingHint.annual_revenue_range)}
                </p>
              </div>
            )}
            {onboardingHint.profile_json &&
              typeof onboardingHint.profile_json === "object" &&
              Object.entries(
                onboardingHint.profile_json as Record<string, unknown>
              ).map(([k, v]) =>
                v ? (
                  <div key={k}>
                    <p className="text-xs text-slate-500">
                      {FIELD_LABELS[k] ?? k.replace(/_/g, " ")}
                    </p>
                    <p className="text-slate-200">{String(v)}</p>
                  </div>
                ) : null
              )}
          </div>
        </Card>
      )}
    </div>
  );
}
