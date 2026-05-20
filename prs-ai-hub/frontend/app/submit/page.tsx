"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ContractDocumentPanel } from "@/components/ContractDocumentPanel";
import { SkuSchedulePanel } from "@/components/SkuSchedulePanel";
import type { SKUItem } from "@/lib/sku";
import {
  FixtureMeta,
  SubmitPayload,
  getFixture,
  listFixtures,
  submitPRS,
} from "@/lib/api";

const EMPTY: SubmitPayload = {
  requestor: {
    requestor_name: "",
    requestor_business_unit: "Procurement",
    business_owner: "",
    business_unit: "Supply Chain",
    business_priority: "High",
    request_description: "",
    need_by_date: "2026-09-01",
  },
  vendor: {
    vendor_name: "",
    vendor_address_line1: "",
    vendor_address_state: "",
    vendor_address_country: "US",
    vendor_contact_name: "",
    vendor_contact_role: "Account Manager",
    vendor_contact_phone_country_code: "+1",
    vendor_contact_phone: "",
    vendor_contact_email: "",
  },
  contract_text: "",
  contract_filename: "contract.txt",
  sku_items: [],
  addendum_text: "",
};

export default function SubmitPage() {
  const router = useRouter();
  const [fixtures, setFixtures] = useState<FixtureMeta[]>([]);
  const [form, setForm] = useState<SubmitPayload>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listFixtures().then(setFixtures).catch(() => {});
    const draft = sessionStorage.getItem("prs_resubmit_draft");
    if (draft) {
      try {
        setForm(normalizePayload(JSON.parse(draft)));
      } catch {
        /* ignore */
      }
      sessionStorage.removeItem("prs_resubmit_draft");
    }
  }, []);

  async function loadFixture(id: string) {
    setError(null);
    try {
      const data = await getFixture(id);
      setForm(normalizePayload(data));
    } catch {
      setError("Could not load fixture. Check that the API is running on port 8000.");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await submitPRS(normalizePayload(form));
      router.push(`/results/${res.request_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setLoading(false);
    }
  }

  function updateRequestor(field: string, value: string) {
    setForm((f) => ({
      ...f,
      requestor: { ...EMPTY.requestor, ...f.requestor, [field]: value },
    }));
  }

  function updateVendor(field: string, value: string) {
    setForm((f) => ({
      ...f,
      vendor: { ...EMPTY.vendor, ...f.vendor, [field]: value },
    }));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Submit PRS</h1>
        <p className="mt-1 text-slate-600">
          Load a sample fixture or fill the form manually.
        </p>
      </div>

      {fixtures.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Sample fixtures</h2>
          <div className="flex flex-wrap gap-2">
            {fixtures.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => loadFixture(f.id)}
                className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-left text-sm hover:bg-brand-100"
              >
                <span className="font-medium text-brand-800">{f.label}</span>
                <span className="mt-0.5 block text-xs text-slate-500">
                  Expected: {f.expected_scenario}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <FormSection title="Requestor">
          <Field label="Name" value={form.requestor?.requestor_name ?? ""} onChange={(v) => updateRequestor("requestor_name", v)} />
          <Field label="Business unit" value={form.requestor?.requestor_business_unit ?? ""} onChange={(v) => updateRequestor("requestor_business_unit", v)} />
          <Field label="Business owner" value={form.requestor?.business_owner ?? ""} onChange={(v) => updateRequestor("business_owner", v)} />
          <Field label="Priority" value={form.requestor?.business_priority ?? ""} onChange={(v) => updateRequestor("business_priority", v)} />
          <Field label="Need by date" value={form.requestor?.need_by_date ?? ""} onChange={(v) => updateRequestor("need_by_date", v)} />
          <label className="block text-sm">
            <span className="font-medium text-slate-700">Description</span>
            <textarea
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              rows={3}
              value={form.requestor?.request_description ?? ""}
              onChange={(e) => updateRequestor("request_description", e.target.value)}
              required
            />
          </label>
        </FormSection>

        <FormSection title="Vendor">
          <Field label="Vendor name" value={form.vendor?.vendor_name ?? ""} onChange={(v) => updateVendor("vendor_name", v)} />
          <Field label="Address" value={form.vendor?.vendor_address_line1 ?? ""} onChange={(v) => updateVendor("vendor_address_line1", v)} />
          <Field label="State" value={form.vendor?.vendor_address_state ?? ""} onChange={(v) => updateVendor("vendor_address_state", v)} />
          <Field label="Contact email" value={form.vendor?.vendor_contact_email ?? ""} onChange={(v) => updateVendor("vendor_contact_email", v)} />
          <Field label="Phone" value={form.vendor?.vendor_contact_phone ?? ""} onChange={(v) => updateVendor("vendor_contact_phone", v)} />
        </FormSection>

        <ContractDocumentPanel
          title="Contract"
          filename={form.contract_filename}
          text={form.contract_text}
          onChange={(name, contractText) =>
            setForm((f) => ({
              ...f,
              contract_filename: name,
              contract_text: contractText,
              addendum_text: f.addendum_text || contractText.slice(0, 8000),
            }))
          }
        />

        <SkuSchedulePanel
          title="SKU schedule"
          items={(form.sku_items || []) as SKUItem[]}
          onChange={(sku_items) => setForm((f) => ({ ...f, sku_items }))}
          addendumText={form.addendum_text || undefined}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading || !form.contract_text}
          className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Submitting…" : "Submit for validation"}
        </button>
      </form>
    </div>
  );
}

function normalizePayload(data: Partial<SubmitPayload>): SubmitPayload {
  return {
    requestor: { ...EMPTY.requestor, ...(data.requestor || {}) },
    vendor: { ...EMPTY.vendor, ...(data.vendor || {}) },
    contract_text: data.contract_text || "",
    contract_filename: data.contract_filename || "contract.txt",
    sku_items: (data.sku_items || []) as SKUItem[],
    addendum_text: data.addendum_text || "",
  };
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      <input
        className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
      />
    </label>
  );
}
