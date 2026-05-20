"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentDetailCard } from "@/components/AgentDetailCard";
import { StatusBadge } from "@/components/StatusBadge";
import {
  evaluateCCRTransaction,
  getCCRTransactions,
  type CCRTransaction,
} from "@/lib/api";

function ccrBadgeStatus(decision: string): string {
  const d = decision.toUpperCase();
  if (d === "PASS_THROUGH") return "pass";
  if (d === "SOFT_EXCEPTION") return "partial";
  if (d === "HARD_EXCEPTION") return "fail";
  return decision || "unknown";
}

export default function CCRPage() {
  const [items, setItems] = useState<CCRTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);
  const [evalMeta, setEvalMeta] = useState<{
    matches_expected: boolean;
    expected: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCCRTransactions()
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const runEvaluate = useCallback(async (transactionId: string) => {
    setSelectedId(transactionId);
    setEvaluating(true);
    setError(null);
    setEvalResult(null);
    setEvalMeta(null);
    try {
      const data = await evaluateCCRTransaction(transactionId);
      setEvalResult(data.result);
      setEvalMeta({
        matches_expected: data.matches_expected,
        expected: data.expected_ccr_decision,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }, []);

  const selected = items.find((i) => i.transaction_id === selectedId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">CCR transactions</h1>
        <p className="mt-1 text-sm text-slate-600">
          Invoice-level decisions from{" "}
          <code className="rounded bg-slate-100 px-1">ccr_decision_input_may2026.xlsx</code>
          , linked to Contract Intelligence text files. One row = one transaction (not one
          contract submission).
        </p>
      </div>

      {loading ? (
        <p className="text-slate-500">Loading transactions…</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-4 py-3">
              <h2 className="font-semibold">Evaluation batch ({items.length})</h2>
            </div>
            <div className="max-h-[32rem] overflow-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-3 py-2">Txn</th>
                    <th className="px-3 py-2">Contract</th>
                    <th className="px-3 py-2">Amount</th>
                    <th className="px-3 py-2">Expected</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr
                      key={row.transaction_id}
                      className={`border-t border-slate-100 ${
                        selectedId === row.transaction_id ? "bg-brand-50" : ""
                      }`}
                    >
                      <td className="px-3 py-2 font-data text-xs">{row.transaction_id}</td>
                      <td className="px-3 py-2 text-xs">
                        {row.contract_number}
                        <br />
                        <span className="text-slate-500">{row.contract_status}</span>
                      </td>
                      <td className="px-3 py-2">
                        {row.invoice_amount_usd != null
                          ? `$${row.invoice_amount_usd.toLocaleString()}`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        {row.expected_ccr_decision ? (
                          <span className="flex flex-col gap-1">
                            <span className="font-data text-xs">
                              {row.expected_ccr_decision}
                            </span>
                            <StatusBadge
                              status={ccrBadgeStatus(row.expected_ccr_decision)}
                            />
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => runEvaluate(row.transaction_id)}
                          disabled={evaluating && selectedId === row.transaction_id}
                          className="text-brand-700 hover:underline disabled:opacity-50"
                        >
                          {evaluating && selectedId === row.transaction_id
                            ? "Running…"
                            : "Evaluate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="space-y-4">
            {selected && (
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
                <h3 className="font-semibold">{selected.transaction_id}</h3>
                <p className="mt-1 text-slate-600">{selected.line_item_description}</p>
                <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <dt className="text-slate-500">Invoice</dt>
                  <dd>{selected.invoice_number}</dd>
                  <dt className="text-slate-500">Contract file</dt>
                  <dd>{selected.contract_filename || "—"}</dd>
                  <dt className="text-slate-500">PRS score</dt>
                  <dd>{selected.prs_completeness_score ?? "—"}</dd>
                </dl>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">
                {error}
              </div>
            )}

            {evalResult && (
              <div className="space-y-3">
                {evalMeta && (
                  <div
                    className={`rounded-lg border p-3 text-sm ${
                      evalMeta.matches_expected
                        ? "border-green-200 bg-green-50 text-green-900"
                        : "border-amber-200 bg-amber-50 text-amber-900"
                    }`}
                  >
                    Expected: <strong>{evalMeta.expected || "—"}</strong>
                    {evalMeta.expected && (
                      <>
                        {" "}
                        · Match: {evalMeta.matches_expected ? "Yes" : "No"}
                      </>
                    )}
                  </div>
                )}
                <AgentDetailCard
                  label="CCR Decision"
                  agentResult={evalResult}
                />
              </div>
            )}

            {!evalResult && !error && (
              <p className="text-sm text-slate-500">
                Select Evaluate on a transaction to run the CCR agent with linked contract
                text.
              </p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
