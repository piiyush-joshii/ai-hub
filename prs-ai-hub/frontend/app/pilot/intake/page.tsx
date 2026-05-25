"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentDetailCard } from "@/components/AgentDetailCard";
import {
  listIntakeSubmissions,
  validateIntakeSubmission,
  type IntakeSubmission,
} from "@/lib/api";

export default function PilotIntakePage() {
  const [items, setItems] = useState<IntakeSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listIntakeSubmissions()
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const runValidate = useCallback(async (key: string) => {
    setSelectedKey(key);
    setValidating(true);
    setError(null);
    setResult(null);
    try {
      const data = await validateIntakeSubmission(key);
      setResult(data.result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setValidating(false);
    }
  }, []);

  const selected = items.find((i) => i.submission_key === selectedKey);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Phase 1 — Intake pilot</h1>
        <p className="mt-1 text-sm text-slate-600">
          Batch-validate Vizient intake rows from{" "}
          <code className="rounded bg-slate-100 px-1">vizient_prs_intake_agent_may0519.xlsx</code>.
          Fail/partial results are queued for human approval.
        </p>
      </div>

      {loading ? (
        <p className="text-slate-500">Loading submissions…</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-4 py-3">
              <h2 className="font-semibold">Submissions ({items.length})</h2>
            </div>
            <ul className="max-h-[32rem] divide-y divide-slate-100 overflow-auto">
              {items.map((row) => (
                <li key={row.submission_key} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-data text-xs font-medium text-slate-800">
                        {row.submission_key}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">{row.line_item_description}</p>
                      <p className="text-xs text-slate-400">
                        ${row.invoice_amount_usd} · {row.contract_number}
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={validating && selectedKey === row.submission_key}
                      onClick={() => runValidate(row.submission_key)}
                      className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                    >
                      {validating && selectedKey === row.submission_key ? "…" : "Validate"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            {selected && (
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
                <h2 className="font-semibold">Selected row</h2>
                <dl className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <dt className="text-slate-500">Supplier</dt>
                  <dd>{selected.supplier_id}</dd>
                  <dt className="text-slate-500">Invoice</dt>
                  <dd>{selected.invoice_number}</dd>
                  <dt className="text-slate-500">Email</dt>
                  <dd className="truncate">{selected.contact_email}</dd>
                </dl>
              </div>
            )}
            {error && <p className="text-sm text-red-600">{error}</p>}
            {result && (
              <AgentDetailCard label="PRS Intake (Vizient row)" agentResult={result} />
            )}
            {!result && !error && selectedKey && !validating && (
              <p className="text-sm text-slate-500">Click Validate to run the intake agent.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
