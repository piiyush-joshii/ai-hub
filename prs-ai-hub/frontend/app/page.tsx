"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { SubmissionRowActions } from "@/components/SubmissionRowActions";
import { getPRSHistory } from "@/lib/api";

export default function DashboardPage() {
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

  function loadHistory() {
    setLoading(true);
    getPRSHistory()
      .then((data) => setItems(data.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const passCount = items.filter((i) => i.overall_status === "pass").length;
  const failCount = items.filter((i) => i.overall_status === "fail").length;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-slate-600">
            Healthcare purchase request & contract validation
          </p>
        </div>
        <Link
          href="/submit"
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-brand-700"
        >
          Submit New PRS
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Total submissions" value={String(items.length)} />
        <StatCard label="Passed" value={String(passCount)} />
        <StatCard label="Failed / blocked" value={String(failCount)} />
      </div>

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 className="font-semibold">Recent submissions</h2>
        </div>
        {loading ? (
          <p className="p-6 text-slate-500">Loading…</p>
        ) : items.length === 0 ? (
          <p className="p-6 text-slate-500">
            No submissions yet.{" "}
            <Link href="/submit" className="text-brand-700 underline">
              Submit your first PRS
            </Link>
          </p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-6 py-3">Request ID</th>
                <th className="px-6 py-3">Vendor</th>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.request_id} className="border-t border-slate-100">
                  <td className="px-6 py-3 font-data text-xs">{row.request_id}</td>
                  <td className="px-6 py-3">{row.vendor_name}</td>
                  <td className="px-6 py-3">
                    {new Date(row.submitted_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-3">
                    <StatusBadge status={row.overall_status || row.status} />
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
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-brand-700">{value}</p>
    </div>
  );
}
