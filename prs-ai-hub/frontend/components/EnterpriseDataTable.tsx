"use client";

type EnterpriseDataTableProps = {
  records: Record<string, unknown>[];
  priorityColumns?: string[];
};

export function EnterpriseDataTable({ records, priorityColumns }: EnterpriseDataTableProps) {
  if (!records.length) {
    return <p className="text-sm text-slate-500">No records in this dataset.</p>;
  }

  const allKeys = new Set<string>();
  for (const row of records) {
    Object.keys(row).forEach((k) => allKeys.add(k));
  }
  const columns = [
    ...(priorityColumns || []).filter((c) => allKeys.has(c)),
    ...Array.from(allKeys).filter((c) => !(priorityColumns || []).includes(c)).sort(),
  ].slice(0, 10);

  return (
    <div className="max-h-[28rem] overflow-auto rounded-lg border border-slate-200">
      <table className="w-full text-left text-xs">
        <thead className="sticky top-0 bg-slate-50 text-slate-600">
          <tr>
            {columns.map((col) => (
              <th key={col} className="whitespace-nowrap px-3 py-2 font-medium">
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((row, i) => (
            <tr key={i} className="border-t border-slate-100">
              {columns.map((col) => (
                <td key={col} className="max-w-[12rem] truncate px-3 py-2">
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}
