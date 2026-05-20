import { StatusBadge } from "@/components/StatusBadge";

function asBulletList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim() !== "");
}

type AgentDetailCardProps = {
  label: string;
  agentResult: Record<string, unknown>;
};

export function AgentDetailCard({ label, agentResult }: AgentDetailCardProps) {
  const bullets = asBulletList(agentResult.bullet_summary);
  const summary = String(agentResult.summary || "");

  return (
    <details className="rounded-lg border border-slate-200 bg-white p-4">
      <summary className="cursor-pointer font-medium">
        {label}{" "}
        <StatusBadge
          status={String(
            agentResult.ccr_decision || agentResult.status || "unknown"
          )}
        />
      </summary>
      {summary && <p className="mt-2 text-sm text-slate-600">{summary}</p>}
      {bullets.length > 0 && (
        <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-800">
          {bullets.map((bullet, i) => (
            <li key={i}>{bullet}</li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-slate-500">
        Full JSON response
      </p>
      <pre className="mt-1 max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs">
        {JSON.stringify(agentResult, null, 2)}
      </pre>
    </details>
  );
}
