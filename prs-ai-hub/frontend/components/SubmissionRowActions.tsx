"use client";

import Link from "next/link";
import { useState } from "react";
import { deletePRS } from "@/lib/api";

type SubmissionRowActionsProps = {
  requestId: string;
  onDeleted: () => void;
};

export function SubmissionRowActions({ requestId, onDeleted }: SubmissionRowActionsProps) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (
      !window.confirm(
        `Delete submission ${requestId}? This cannot be undone.`
      )
    ) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await deletePRS(requestId);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-3">
        <Link href={`/results/${requestId}`} className="text-brand-700 hover:underline">
          View
        </Link>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          className="text-red-600 hover:text-red-800 disabled:opacity-50"
        >
          {deleting ? "Deleting…" : "Delete"}
        </button>
      </div>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
