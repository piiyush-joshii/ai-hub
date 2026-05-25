"use client";

import { useCallback, useEffect, useState } from "react";
import { AgentDetailCard } from "@/components/AgentDetailCard";
import { composeSupplierMessage, listSupplierMessages } from "@/lib/api";

export default function SupplierPage() {
  const [items, setItems] = useState<Record<string, string>[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [composing, setComposing] = useState(false);
  const [draft, setDraft] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSupplierMessages()
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const runCompose = useCallback(async (messageId: string) => {
    setSelectedId(messageId);
    setComposing(true);
    setError(null);
    setDraft(null);
    try {
      const data = await composeSupplierMessage(messageId);
      setDraft(data.draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compose failed");
    } finally {
      setComposing(false);
    }
  }, []);

  const selected = items.find((m) => m.message_id === selectedId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Supplier interaction</h1>
        <p className="mt-1 text-sm text-slate-600">
          Phase 1 — draft correction/remittance emails from{" "}
          <code className="rounded bg-slate-100 px-1">supplier_interaction_inputFile_0519.xlsx</code>.
          Messages are not sent; drafts go to the approval queue when required.
        </p>
      </div>

      {loading ? (
        <p className="text-slate-500">Loading message queue…</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-4 py-3">
              <h2 className="font-semibold">Message queue ({items.length})</h2>
            </div>
            <ul className="max-h-[32rem] divide-y divide-slate-100 overflow-auto">
              {items.map((msg) => (
                <li key={msg.message_id} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-data text-xs font-medium">{msg.message_id}</p>
                      <p className="text-xs text-slate-600">{msg.supplier_name}</p>
                      <p className="text-xs text-slate-400">
                        {msg.communication_type} · {msg.message_status}
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={composing && selectedId === msg.message_id}
                      onClick={() => runCompose(msg.message_id)}
                      className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                    >
                      {composing && selectedId === msg.message_id ? "…" : "Draft"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-4">
            {selected && (
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600">
                <p>
                  <strong>To:</strong> {selected.contact_email}
                </p>
                <p className="mt-1">
                  <strong>Context:</strong> {selected.key_context_variables}
                </p>
              </div>
            )}
            {error && <p className="text-sm text-red-600">{error}</p>}
            {draft && (
              <>
                {typeof draft.subject === "string" && (
                  <div className="rounded-xl border border-brand-100 bg-brand-50/40 p-4">
                    <p className="text-xs font-medium text-slate-500">Subject</p>
                    <p className="text-sm font-medium text-slate-900">{draft.subject}</p>
                  </div>
                )}
                {typeof draft.body_plain === "string" && (
                  <pre className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">
                    {draft.body_plain}
                  </pre>
                )}
                <AgentDetailCard label="Supplier interaction agent" agentResult={draft} />
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
