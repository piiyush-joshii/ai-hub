"use client";

import { useCallback, useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import {
  approveItem,
  listApprovals,
  rejectItem,
  type ApprovalItem,
} from "@/lib/api";

export default function ApprovalsPage() {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    listApprovals()
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function decide(refId: string, action: "approve" | "reject") {
    setBusy(refId);
    setError(null);
    try {
      if (action === "approve") await approveItem(refId);
      else await rejectItem(refId);
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Approval queue</h1>
        <p className="mt-1 text-sm text-slate-600">
          Phase 0 supervised pilot — review PRS submissions, intake failures, CCR hard
          exceptions, and supplier drafts before progressing.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : items.length === 0 ? (
        <p className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          No pending approvals. Submit a PRS, validate intake, evaluate CCR, or compose a
          supplier message to create items.
        </p>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.ref_id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.item_type} · {item.ref_id}
                  </p>
                  {item.agent_result && (
                    <p className="mt-2 text-xs text-slate-600">
                      Agent status:{" "}
                      <StatusBadge
                        status={
                          (item.agent_result.overall_status as string) ||
                          (item.agent_result.status as string) ||
                          (item.agent_result.ccr_decision as string) ||
                          "partial"
                        }
                      />
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={busy === item.ref_id}
                    onClick={() => decide(item.ref_id, "approve")}
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busy === item.ref_id}
                    onClick={() => decide(item.ref_id, "reject")}
                    className="rounded-lg border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
