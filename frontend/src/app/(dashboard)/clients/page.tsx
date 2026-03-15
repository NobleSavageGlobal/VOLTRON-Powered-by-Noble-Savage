"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  useClients,
  useCreateClient,
  useDeleteClient,
} from "@/hooks/useClients";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { Plus, Building2, User, Trash2, Upload } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { Client, ClientEntityType } from "@/lib/types";

const ENTITY_TYPES: { value: ClientEntityType; label: string }[] = [
  { value: "person", label: "Individual" },
  { value: "business", label: "Business" },
  { value: "trust", label: "Trust" },
  { value: "other", label: "Other" },
];

const REVENUE_RANGES = [
  "Under $50K",
  "$50K–$100K",
  "$100K–$250K",
  "$250K–$500K",
  "$500K–$1M",
  "Over $1M",
];

const createSchema = z.object({
  display_name: z.string().min(2, "Name must be at least 2 characters"),
  entity_type: z.enum(["person", "business", "trust", "other"]),
  industry: z.string().optional(),
  annual_revenue_range: z.string().optional(),
});

type CreateForm = z.infer<typeof createSchema>;

function ClientCard({
  client,
  onDeleteRequest,
}: {
  client: Client;
  onDeleteRequest: (client: Client) => void;
}) {
  const isActive = client.status === "active";
  const Icon = client.entity_type === "person" ? User : Building2;

  return (
    <Card className="p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 flex items-center justify-center flex-shrink-0">
            <Icon className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-slate-100 truncate">
              {client.display_name}
            </div>
            <div className="text-xs text-slate-500 capitalize">
              {client.entity_type}
            </div>
          </div>
        </div>
        <Badge
          label={client.status}
          colorClass={
            isActive
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-slate-700 text-slate-400"
          }
        />
      </div>

      {(client.industry || client.annual_revenue_range) && (
        <div className="flex flex-wrap gap-2 text-xs text-slate-400">
          {client.industry && <span>🏭 {client.industry}</span>}
          {client.annual_revenue_range && (
            <span>💰 {client.annual_revenue_range}</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between pt-1 border-t border-slate-800">
        <span className="text-xs text-slate-600">
          Added {formatDate(client.created_at)}
        </span>
        <button
          onClick={() => onDeleteRequest(client)}
          className="p-1.5 rounded text-slate-600 hover:text-red-400 hover:bg-red-400/10 transition"
          title="Deactivate client"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </Card>
  );
}

export default function ClientsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [showUploadOnboard, setShowUploadOnboard] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Client | null>(null);
  const [statusFilter, setStatusFilter] = useState<"active" | "inactive" | "">(
    "active",
  );

  const { data: clients, isLoading } = useClients(
    statusFilter ? { status: statusFilter } : undefined,
  );
  const createClient = useCreateClient();
  const deleteClient = useDeleteClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: { entity_type: "person" },
  });

  const onSubmit = async (values: CreateForm) => {
    await createClient.mutateAsync({
      display_name: values.display_name,
      entity_type: values.entity_type,
      industry: values.industry || undefined,
      annual_revenue_range: values.annual_revenue_range || undefined,
    });
    reset();
    setShowCreate(false);
  };

  const handleConfirmDelete = () => {
    if (pendingDelete) {
      deleteClient.mutate(pendingDelete.id);
      setPendingDelete(null);
    }
  };

  const activeCount = clients?.filter((c) => c.status === "active").length ?? 0;

  return (
    <div className="flex flex-col flex-1">
      <Header title="Clients" subtitle="Manage your client portfolio" />

      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">
              {clients
                ? `${activeCount} active client${activeCount !== 1 ? "s" : ""}`
                : ""}
            </span>
            <div className="flex gap-1 ml-2">
              {(["active", "inactive", ""] as const).map((s) => (
                <button
                  key={s || "all"}
                  onClick={() => setStatusFilter(s)}
                  className={`px-3 py-1 rounded text-xs font-medium transition ${
                    statusFilter === s
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={() => setShowUploadOnboard(true)}
              size="sm"
            >
              <Upload className="w-4 h-4 mr-1.5" />
              Start With Upload
            </Button>
            <Button onClick={() => setShowCreate(true)} size="sm">
              <Plus className="w-4 h-4 mr-1.5" />
              Add Client
            </Button>
          </div>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : !clients || clients.length === 0 ? (
          <Card className="p-12 text-center">
            <Building2 className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <div className="text-slate-400 font-medium">No clients yet</div>
            <div className="text-slate-600 text-sm mt-1">
              Add your first client to start tracking financial data, documents,
              and action plans.
            </div>
            <Button
              onClick={() => setShowCreate(true)}
              size="sm"
              className="mt-4"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add First Client
            </Button>
            <Button
              onClick={() => setShowUploadOnboard(true)}
              size="sm"
              variant="secondary"
              className="mt-2"
            >
              <Upload className="w-4 h-4 mr-1.5" />
              Start With Upload
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {clients.map((c) => (
              <ClientCard
                key={c.id}
                client={c}
                onDeleteRequest={setPendingDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="Add New Client"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Full Name / Business Name *
            </label>
            <Input
              {...register("display_name")}
              placeholder="e.g. John Smith or Acme LLC"
              error={errors.display_name?.message}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Client Type
            </label>
            <select
              {...register("entity_type")}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ENTITY_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Industry
            </label>
            <Input
              {...register("industry")}
              placeholder="e.g. Real Estate, Technology, Retail"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Annual Revenue Range
            </label>
            <select
              {...register("annual_revenue_range")}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select range...</option>
              {REVENUE_RANGES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                reset();
                setShowCreate(false);
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding..." : "Add Client"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Deactivate Confirmation Modal */}
      <Modal
        isOpen={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        title="Deactivate Client"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-300">
            Are you sure you want to deactivate{" "}
            <span className="font-semibold text-slate-100">
              {pendingDelete?.display_name}
            </span>
            ? The client record will be preserved but marked as inactive.
          </p>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete}>
              Deactivate
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={showUploadOnboard}
        onClose={() => setShowUploadOnboard(false)}
        title="Onboard Client From Documents"
        className="max-w-2xl"
      >
        <div className="space-y-3">
          <p className="text-sm text-slate-400">
            Upload one or more files and we will extract onboarding fields to
            create or update client records automatically.
          </p>
          <DocumentUpload
            defaultAutoOnboard
            lockAutoOnboard
            onSuccess={() => {
              setShowUploadOnboard(false);
            }}
          />
        </div>
      </Modal>
    </div>
  );
}
