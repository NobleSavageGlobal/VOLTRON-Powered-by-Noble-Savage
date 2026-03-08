"use client";

import { Calendar, AlertTriangle, Lightbulb, Database } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import type { Document } from "@/lib/types";

interface ExtractedDataViewProps {
  document: Document;
}

export function ExtractedDataView({ document: doc }: ExtractedDataViewProps) {
  const onboardingHint =
    doc.extracted_data && typeof doc.extracted_data.onboarding_hint === "object"
      ? (doc.extracted_data.onboarding_hint as Record<string, unknown>)
      : null;

  return (
    <div className="space-y-4">
      {/* AI Summary */}
      {doc.ai_summary && (
        <Card>
          <CardHeader>
            <CardTitle>AI Summary</CardTitle>
          </CardHeader>
          <p className="text-sm text-slate-300 leading-relaxed">
            {doc.ai_summary}
          </p>
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
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="font-mono text-indigo-300 flex-shrink-0">
                  {kd.date}
                </span>
                <span className="text-slate-400">{kd.description}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Risks */}
      {doc.risks && doc.risks.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <CardTitle>Identified Risks</CardTitle>
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

      {/* Opportunities */}
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

      {/* Raw Extracted Data */}
      {doc.extracted_data && Object.keys(doc.extracted_data).length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-slate-400" />
              <CardTitle>Extracted Fields</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-2">
            {Object.entries(doc.extracted_data).map(([key, val]) => (
              <div key={key} className="flex gap-3 text-sm">
                <span className="text-slate-400 capitalize flex-shrink-0 w-32 truncate">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="text-slate-200">{String(val)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {onboardingHint && (
        <Card>
          <CardHeader>
            <CardTitle>Onboarding Suggestions</CardTitle>
          </CardHeader>
          <div className="space-y-2 text-sm">
            <div className="flex gap-3">
              <span className="text-slate-400 w-36">Display name</span>
              <span className="text-slate-200">
                {String(onboardingHint.display_name ?? "")}
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-slate-400 w-36">Entity type</span>
              <span className="text-slate-200">
                {String(onboardingHint.entity_type ?? "")}
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-slate-400 w-36">Industry</span>
              <span className="text-slate-200">
                {String(onboardingHint.industry ?? "")}
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-slate-400 w-36">Revenue range</span>
              <span className="text-slate-200">
                {String(onboardingHint.annual_revenue_range ?? "")}
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
