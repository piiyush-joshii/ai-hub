"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { SubmissionRowActions } from "@/components/SubmissionRowActions";
import { getPRSHistory } from "@/lib/api";

export default function HistoryPage() {
  const [items, setItems] = useState<
    {
      request_id: string;
      submitted_at: string;
      status: string;
      overall_status?: string;
      vendor_name: string;
    }[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPRSHistory(1)
      .then((data) => setItems(data.items || []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Submission history</h1>
      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <table className="w-full rounded-xl border border-slate-200 bg-white text-left text-sm shadow-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-6 py-3">Request ID</th>
              <th className="px-6 py-3">Vendor</th>
              <th className="px-6 py-3">Submitted</th>
              <th className="px-6 py-3">Job status</th>
              <th className="px-6 py-3">Validation</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.request_id} className="border-t border-slate-100">
                <td className="px-6 py-3 font-data text-xs">{row.request_id}</td>
                <td className="px-6 py-3">{row.vendor_name}</td>
                <td className="px-6 py-3">
                  {new Date(row.submitted_at).toLocaleString()}
                </td>
                <td className="px-6 py-3">
                  <StatusBadge status={row.status} />
                </td>
                <td className="px-6 py-3">
                  <StatusBadge status={row.overall_status || "—"} />
                </td>
                <td className="px-6 py-3">
                  <SubmissionRowActions
                    requestId={row.request_id}
                    onDeleted={() =>
                      setItems((prev) => prev.filter((i) => i.request_id !== row.request_id))
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
