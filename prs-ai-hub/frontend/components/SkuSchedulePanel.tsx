"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { EMPTY_SKU, SKU_STATUSES, SKU_UOMS, type SKUItem } from "@/lib/sku";

export type SkuValidationResult = {
  sku_number: string;
  status: string;
  errors?: string[];
  warnings?: string[];
};

type Props = {
  title?: string;
  items: SKUItem[];
  onChange?: (items: SKUItem[]) => void;
  readOnly?: boolean;
  validationResults?: SkuValidationResult[];
  addendumText?: string;
};

export function SkuSchedulePanel({
  title = "SKU schedule",
  items,
  onChange,
  readOnly = false,
  validationResults = [],
  addendumText,
}: Props) {
  const [showAddendum, setShowAddendum] = useState(false);
  const validationMap = Object.fromEntries(
    validationResults.map((r) => [r.sku_number, r])
  );

  function updateItem(index: number, patch: Partial<SKUItem>) {
    if (!onChange) return;
    const next = items.map((row, i) => (i === index ? { ...row, ...patch } : row));
    onChange(next);
  }

  function addRow() {
    if (!onChange) return;
    onChange([...items, { ...EMPTY_SKU, sku_number: `SKU-${items.length + 1}` }]);
  }

  function removeRow(index: number) {
    if (!onChange) return;
    onChange(items.filter((_, i) => i !== index));
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="mt-1 text-xs text-slate-500">
            {items.length} line item{items.length === 1 ? "" : "s"}
            {readOnly ? " (submitted)" : " — edit before submit"}
          </p>
        </div>
        {!readOnly && onChange && (
          <button
            type="button"
            onClick={addRow}
            className="rounded-lg border border-brand-300 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-800 hover:bg-brand-100"
          >
            + Add SKU row
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No SKU line items. Load a fixture or add rows manually.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
              <tr>
                {validationResults.length > 0 && <th className="px-3 py-2">Validation</th>}
                <th className="px-3 py-2">SKU #</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2">UOM</th>
                <th className="px-3 py-2">Unit price</th>
                <th className="px-3 py-2">MSRP</th>
                <th className="px-3 py-2">MOQ</th>
                <th className="px-3 py-2">Lead time</th>
                <th className="px-3 py-2">Status</th>
                {!readOnly && <th className="px-3 py-2"></th>}
              </tr>
            </thead>
            <tbody>
              {items.map((row, index) => {
                const vr = validationMap[row.sku_number];
                return (
                  <tr key={`${row.sku_number}-${index}`} className="border-t border-slate-100">
                    {validationResults.length > 0 && (
                      <td className="px-3 py-2">
                        {vr ? (
                          <StatusBadge status={vr.status} />
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    )}
                    <td className="px-3 py-2 font-data text-xs">
                      {readOnly ? (
                        row.sku_number
                      ) : (
                        <input
                          className="w-28 rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.sku_number}
                          onChange={(e) => updateItem(index, { sku_number: e.target.value })}
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.description
                      ) : (
                        <input
                          className="w-full min-w-[140px] rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.description}
                          onChange={(e) => updateItem(index, { description: e.target.value })}
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.unit_of_measure
                      ) : (
                        <select
                          className="rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.unit_of_measure}
                          onChange={(e) => updateItem(index, { unit_of_measure: e.target.value })}
                        >
                          {SKU_UOMS.map((u) => (
                            <option key={u} value={u}>
                              {u}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        formatMoney(row.unit_price)
                      ) : (
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          className="w-24 rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.unit_price || ""}
                          onChange={(e) =>
                            updateItem(index, { unit_price: parseFloat(e.target.value) || 0 })
                          }
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.msrp != null ? formatMoney(row.msrp) : "—"
                      ) : (
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          className="w-24 rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.msrp ?? ""}
                          onChange={(e) =>
                            updateItem(index, {
                              msrp: e.target.value === "" ? null : parseFloat(e.target.value),
                            })
                          }
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.min_order_qty
                      ) : (
                        <input
                          type="number"
                          min={1}
                          className="w-16 rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.min_order_qty || ""}
                          onChange={(e) =>
                            updateItem(index, {
                              min_order_qty: parseInt(e.target.value, 10) || 1,
                            })
                          }
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.lead_time
                      ) : (
                        <input
                          className="w-24 rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.lead_time}
                          onChange={(e) => updateItem(index, { lead_time: e.target.value })}
                        />
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {readOnly ? (
                        row.status
                      ) : (
                        <select
                          className="rounded border border-slate-300 px-2 py-1 text-xs"
                          value={row.status}
                          onChange={(e) => updateItem(index, { status: e.target.value })}
                        >
                          {SKU_STATUSES.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    {!readOnly && (
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => removeRow(index)}
                          className="text-xs text-red-600 hover:underline"
                        >
                          Remove
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {validationResults.some((r) => r.errors?.length || r.warnings?.length) && (
        <div className="mt-4 space-y-2 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs">
          <p className="font-medium text-slate-700">Per-SKU validation notes</p>
          {validationResults.map((r) =>
            (r.errors?.length || r.warnings?.length) ? (
              <div key={r.sku_number} className="border-t border-slate-200 pt-2 first:border-0 first:pt-0">
                <span className="font-data font-medium">{r.sku_number}</span>
                {r.errors?.map((e, i) => (
                  <p key={`e-${i}`} className="text-red-700">
                    {e}
                  </p>
                ))}
                {r.warnings?.map((w, i) => (
                  <p key={`w-${i}`} className="text-amber-700">
                    {w}
                  </p>
                ))}
              </div>
            ) : null
          )}
        </div>
      )}

      {addendumText && (
        <div className="mt-4">
          <button
            type="button"
            onClick={() => setShowAddendum((v) => !v)}
            className="text-sm font-medium text-brand-700 hover:underline"
          >
            {showAddendum ? "Hide" : "Show"} addendum / policy text (
            {addendumText.length.toLocaleString()} chars)
          </button>
          {showAddendum && (
            <pre className="font-data mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
              {addendumText}
            </pre>
          )}
        </div>
      )}
    </section>
  );
}

function formatMoney(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n);
}
