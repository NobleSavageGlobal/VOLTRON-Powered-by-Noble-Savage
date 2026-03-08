'use client';

import { Header } from '@/components/layout/Header';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { useDocuments } from '@/hooks/useDocuments';
import { useKnowledgeSearch, useIndexDocument } from '@/hooks/useKnowledge';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { Search, Database, Brain, Sparkles } from 'lucide-react';
import { useState, useDeferredValue } from 'react';

export default function KnowledgePage() {
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const { data: docsData, isLoading: docsLoading } = useDocuments({ status: 'processed', page_size: 50 });
  const { data: searchResults, isFetching: searchFetching } = useKnowledgeSearch(deferredSearch, { limit: 20 });
  const indexDocument = useIndexDocument();

  const isSearchActive = deferredSearch.length > 0;

  return (
    <div className="flex flex-col flex-1">
      <Header title="Knowledge Vault" subtitle="Semantic search across all your documents" />
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Semantic search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ask a question or search across all documents..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {searchFetching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Spinner size="sm" />
            </div>
          )}
        </div>

        {/* Semantic search results */}
        {isSearchActive && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <CardTitle>Search Results</CardTitle>
                {searchResults && (
                  <Badge
                    label={`${searchResults.length} match${searchResults.length !== 1 ? 'es' : ''}`}
                    colorClass="text-purple-400 bg-purple-400/10"
                  />
                )}
              </div>
            </CardHeader>
            {searchFetching ? (
              <div className="flex justify-center py-8"><Spinner /></div>
            ) : searchResults && searchResults.length > 0 ? (
              <div className="space-y-3">
                {searchResults.map((result: { chunk_id: string; text: string; score: number; document_id: string; page?: number }) => (
                  <div
                    key={result.chunk_id}
                    className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      <span className="text-xs text-slate-500">
                        Relevance: {Math.round(result.score * 100)}%
                      </span>
                      {result.page != null && (
                        <span className="text-xs text-slate-600">Page {result.page}</span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{result.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 text-center py-6">
                No matches found for &ldquo;{deferredSearch}&rdquo;
              </p>
            )}
          </Card>
        )}

        {/* Indexed documents */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <CardTitle>Indexed Documents</CardTitle>
            </div>
          </CardHeader>
          {docsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <div className="space-y-2">
              {(docsData?.items ?? []).map((doc) => (
                <div key={doc.id} className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <DocumentCard document={doc} />
                  </div>
                  <button
                    onClick={() => indexDocument.mutate(doc.id)}
                    disabled={indexDocument.isPending}
                    className="px-2.5 py-1 text-xs rounded bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 transition flex-shrink-0"
                    title="Re-index this document"
                  >
                    Index
                  </button>
                </div>
              ))}
              {(docsData?.items ?? []).length === 0 && (
                <p className="text-sm text-slate-500 text-center py-6">
                  No processed documents available for search
                </p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
