import clsx from "clsx";

const styles: Record<string, string> = {
  pass: "bg-green-100 text-green-800 border-green-200",
  partial: "bg-amber-100 text-amber-800 border-amber-200",
  fail: "bg-red-100 text-red-800 border-red-200",
  pending: "bg-slate-100 text-slate-600 border-slate-200",
  processing: "bg-blue-100 text-blue-800 border-blue-200",
  complete: "bg-green-100 text-green-800 border-green-200",
  pass_through: "bg-green-100 text-green-800 border-green-200",
  soft_exception: "bg-amber-100 text-amber-800 border-amber-200",
  hard_exception: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-slate-100 text-slate-600 border-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  const key = (status || "unknown").toLowerCase();
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide",
        styles[key] || styles.unknown
      )}
    >
      {status}
    </span>
  );
}
