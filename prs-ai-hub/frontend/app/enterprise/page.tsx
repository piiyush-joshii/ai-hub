"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { EnterpriseDataTable } from "@/components/EnterpriseDataTable";
import { api } from "@/lib/api";

type DatasetMeta = {
  id: string;
  label: string;
  agent: string;
  source_file: string;
  count: number;
  use: string;
  action?: string;
};

const PRIORITY_COLS: Record<string, string[]> = {
  intake_submissions: [
    "supplier_id",
    "contract_number",
    "invoice_number",
    "invoice_amount_usd",
    "report_period",
  ],
  ccr_transactions: [
    "transaction_id",
    "contract_number",
    "invoice_amount_usd",
    "contract_status",
    "expected_ccr_decision",
  ],
  workflows_active: ["workflow_id", "supplier_name", "current_stage", "workflow_status"],
  cash_invoices: ["invoice_id", "contract_number", "invoice_amount_usd", "ccr_decision"],
  cash_payments: ["payment_id", "payment_amount_usd", "payment_date"],
  exceptions_queue: ["exception_id", "exception_type", "supplier_name", "priority"],
  supplier_messages: ["message_id", "communication_type", "supplier_name", "trigger_source"],
  learning_corrections: ["feedback_id", "source_agent", "human_decision", "override_category"],
};

export default function EnterprisePage() {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [pipeline, setPipeline] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string>("ccr_transactions");
  const [records, setRecords] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/enterprise/manifest")
      .then((res) => {
        setDatasets(res.data.datasets || []);
        setPipeline(res.data.pipeline_order || []);
        setSelectedId(res.data.pipeline_order?.[1] || "ccr_transactions");
      })
      .catch((e) => setError(e.message || "Failed to load manifest"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api
      .get(`/enterprise/datasets/${selectedId}`)
      .then((res) => setRecords(res.data.records || []))
      .catch(() => setRecords([]));
  }, [selectedId]);

  const selected = datasets.find((d) => d.id === selectedId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Enterprise data</h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-600">
          Browse synced test data from the six workbooks in{" "}
          <code className="rounded bg-slate-100 px-1">ai-hub/data/*.xlsx</code>. Each
          dataset maps to a different agent in the full pipeline. Run{" "}
          <code className="rounded bg-slate-100 px-1">python scripts/sync_enterprise_data.py</code>{" "}
          after updating Excel files.
        </p>
      </div>

      <section className="rounded-xl border border-brand-100 bg-brand-50/50 p-4">
        <h2 className="text-sm font-semibold text-brand-900">Pipeline order</h2>
        <ol className="mt-2 flex flex-wrap gap-2 text-xs text-brand-800">
          {pipeline.map((id, i) => (
            <li key={id}>
              <button
                type="button"
                onClick={() => setSelectedId(id)}
                className={`rounded-full border px-3 py-1 ${
                  selectedId === id
                    ? "border-brand-600 bg-brand-600 text-white"
                    : "border-brand-200 bg-white hover:bg-brand-50"
                }`}
              >
                {i + 1}. {datasets.find((d) => d.id === id)?.label || id}
              </button>
            </li>
          ))}
        </ol>
      </section>

      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-2">
            {datasets.map((ds) => (
              <button
                key={ds.id}
                type="button"
                onClick={() => setSelectedId(ds.id)}
                className={`w-full rounded-lg border p-3 text-left text-sm transition-colors ${
                  selectedId === ds.id
                    ? "border-brand-600 bg-white shadow-sm"
                    : "border-slate-200 bg-white hover:border-slate-300"
                }`}
              >
                <p className="font-medium text-slate-900">{ds.label}</p>
                <p className="mt-1 text-xs text-slate-500">{ds.agent}</p>
                <p className="mt-1 font-data text-xs text-slate-400">{ds.count} rows</p>
              </button>
            ))}
          </aside>

          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            {selected && (
              <>
                <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{selected.label}</h2>
                    <p className="mt-1 text-sm text-slate-600">{selected.use}</p>
                    <p className="mt-1 font-data text-xs text-slate-400">
                      Source: {selected.source_file}
                    </p>
                  </div>
                  {selected.id === "ccr_transactions" && (
                    <Link
                      href="/ccr"
                      className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                    >
                      Run CCR agent →
                    </Link>
                  )}
                </div>
                <EnterpriseDataTable
                  records={records}
                  priorityColumns={PRIORITY_COLS[selected.id]}
                />
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
