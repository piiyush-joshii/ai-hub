"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ContractDocumentPanel } from "@/components/ContractDocumentPanel";
import { SkuSchedulePanel, type SkuValidationResult } from "@/components/SkuSchedulePanel";
import type { SKUItem } from "@/lib/sku";
import { AgentDetailCard } from "@/components/AgentDetailCard";
import { StatusBadge } from "@/components/StatusBadge";
import { getPRSRequest, getPRSStatus, wsUrl } from "@/lib/api";
import { formatValidationError } from "@/lib/formatError";
import type { SubmitPayload } from "@/lib/api";

const AGENT_LABELS: Record<string, string> = {
  requestor_info: "Requestor Info",
  vendor_info: "Vendor Info",
  parties_and_definitions: "Parties & Definitions",
  commercial_terms: "Commercial Terms",
  legal_clauses: "Legal Clauses",
  sku_schedule: "SKU Schedule",
  sku_policy: "SKU Policy",
};

const AGENT_ORDER = Object.keys(AGENT_LABELS);

type AgentResultsMap = Record<string, Record<string, unknown>>;

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = params.id as string;
  const [status, setStatus] = useState("pending");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [agentProgress, setAgentProgress] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<SubmitPayload | null>(null);

  const applyResult = useCallback((data: Record<string, unknown>) => {
    setResult(data);
    setStatus("complete");
    const agents = (data.agents as Record<string, string>) || {};
    setAgentProgress(agents);
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    async function poll() {
      try {
        const data = await getPRSStatus(requestId);
        setStatus(data.status);
        if (data.result) applyResult(data.result);
        if (data.error) setError(formatValidationError(data.error));
      } catch {
        /* ignore */
      }
    }

    getPRSRequest(requestId)
      .then((d) => setPayload(d.payload))
      .catch(() => {});

    poll();
    pollTimer = setInterval(poll, 4000);

    try {
      ws = new WebSocket(wsUrl(requestId));
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.event === "agent_complete") {
          setAgentProgress((p) => ({ ...p, [msg.agent]: msg.status }));
        }
        if (msg.event === "validation_complete") {
          applyResult(msg.result);
        }
        if (msg.event === "validation_failed") {
          setError(formatValidationError(String(msg.error || "")));
          setStatus("failed");
        }
      };
    } catch {
      /* ws optional */
    }

    return () => {
      if (pollTimer) clearInterval(pollTimer);
      ws?.close();
    };
  }, [requestId, applyResult]);

  const overall = (result?.overall_status as string) || status;
  const blockers = (result?.critical_blockers as string[]) || [];
  const warnings = (result?.warnings as string[]) || [];
  const agentResults = (result?.agent_results as AgentResultsMap) || {};
  const skuSchedule = agentResults.sku_schedule as Record<string, unknown> | undefined;
  const skuValidationResults = (skuSchedule?.sku_results as SkuValidationResult[]) || [];

  return (
    <div className="space-y-6">
      <div>
        <p className="font-data text-xs text-slate-500">{requestId}</p>
        <h1 className="text-2xl font-bold">Validation Results</h1>
      </div>

      <div
        className={`rounded-xl border p-6 ${
          overall === "pass"
            ? "border-green-200 bg-green-50"
            : overall === "partial"
              ? "border-amber-200 bg-amber-50"
              : "border-red-200 bg-red-50"
        }`}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Overall status</h2>
          <StatusBadge status={overall} />
        </div>
        {status === "processing" && (
          <p className="mt-2 text-sm text-slate-600">
            Running 7 AI agents… this may take 1–2 minutes.
          </p>
        )}
        {result?.next_action != null && (
          <p className="mt-2 text-sm">{String(result.next_action)}</p>
        )}
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 font-semibold">Agent progress</h2>
        <ul className="space-y-2">
          {AGENT_ORDER.map((key) => (
            <li
              key={key}
              className="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-2"
            >
              <span className="text-sm">{AGENT_LABELS[key]}</span>
              <StatusBadge status={agentProgress[key] || "pending"} />
            </li>
          ))}
        </ul>
      </section>

      {payload &&
        (payload.contract_text || (payload.sku_items?.length ?? 0) > 0) && (
        <div className="space-y-3">
          {payload?.contract_text && (
            <ContractDocumentPanel
              title="Submitted contract"
              filename={payload.contract_filename || "contract.txt"}
              text={payload.contract_text}
              onChange={() => {}}
              readOnly
            />
          )}
          {(payload?.sku_items?.length ?? 0) > 0 && (
            <SkuSchedulePanel
              title="Submitted SKU schedule"
              items={payload.sku_items as SKUItem[]}
              readOnly
              validationResults={skuValidationResults}
              addendumText={payload.addendum_text || undefined}
            />
          )}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                sessionStorage.setItem("prs_resubmit_draft", JSON.stringify(payload));
                router.push("/submit");
              }}
              className="rounded-lg border border-brand-600 px-4 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
            >
              Revise & resubmit
            </button>
            <Link
              href="/submit"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              New submission
            </Link>
          </div>
        </div>
        )}

      {(blockers.length > 0 || warnings.length > 0) && (
        <div className="grid gap-4 md:grid-cols-2">
          {blockers.length > 0 && (
            <section className="rounded-xl border border-red-200 bg-red-50 p-4">
              <h3 className="font-semibold text-red-800">Critical blockers</h3>
              <ul className="mt-2 list-inside list-disc text-sm text-red-900">
                {blockers.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </section>
          )}
          {warnings.length > 0 && (
            <section className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <h3 className="font-semibold text-amber-800">Warnings</h3>
              <ul className="mt-2 list-inside list-disc text-sm text-amber-900">
                {warnings.slice(0, 12).map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      {Object.keys(agentResults).length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold">Agent details</h2>
          {AGENT_ORDER.filter((k) => agentResults[k]).map((key) => (
            <AgentDetailCard
              key={key}
              label={AGENT_LABELS[key]}
              agentResult={agentResults[key]}
            />
          ))}
        </section>
      )}

      {error && (
        <section className="rounded-xl border border-red-200 bg-red-50 p-4">
          <h3 className="font-semibold text-red-800">Validation failed</h3>
          <p className="mt-2 text-sm text-red-900">{error}</p>
        </section>
      )}
    </div>
  );
}
