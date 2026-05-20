import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

export function wsUrl(requestId: string): string {
  return `${WS_URL}/api/v1/prs/ws/${requestId}`;
}

export interface FixtureMeta {
  id: string;
  label: string;
  description: string;
  contract_file: string;
  expected_scenario: string;
}

import type { SKUItem } from "@/lib/sku";

export type { SKUItem };

export interface SubmitPayload {
  requestor: Record<string, string>;
  vendor: Record<string, string | null | undefined>;
  contract_text: string;
  contract_filename: string;
  sku_items: SKUItem[];
  addendum_text: string;
}

export interface CCRTransaction {
  transaction_id: string;
  supplier_id: string;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount_usd: number | null;
  contract_number: string;
  contract_status: string;
  contract_filename?: string;
  expected_ccr_decision?: string;
  prs_completeness_score?: number | null;
  line_item_description?: string;
}

export async function listFixtures() {
  const { data } = await api.get<{ fixtures: FixtureMeta[] }>("/fixtures");
  return data.fixtures;
}

export async function getFixture(id: string) {
  const { data } = await api.get<SubmitPayload>(`/fixtures/${id}`);
  return data;
}

export async function submitPRS(payload: SubmitPayload) {
  const { data } = await api.post<{
    success: boolean;
    request_id: string;
    status_url: string;
  }>("/prs/submit", payload);
  return data;
}

export async function getPRSStatus(requestId: string) {
  const { data } = await api.get(`/prs/status/${requestId}`);
  return data;
}

export async function getPRSRequest(requestId: string) {
  const { data } = await api.get<{
    request_id: string;
    status: string;
    submitted_at: string;
    payload: SubmitPayload;
    result: Record<string, unknown> | null;
    error: string | null;
  }>(`/prs/${requestId}`);
  return data;
}

export async function parseDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  try {
    const { data } = await api.post<{
      filename: string;
      text: string;
      char_count: number;
    }>("/prs/parse-document", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (err: unknown) {
    if (axios.isAxiosError(err) && err.response?.data?.detail) {
      const d = err.response.data.detail;
      throw new Error(typeof d === "string" ? d : JSON.stringify(d));
    }
    throw err;
  }
}

export async function getPRSHistory(page = 1) {
  const { data } = await api.get("/prs/history", { params: { page, limit: 20 } });
  return data;
}

export async function deletePRS(requestId: string) {
  const { data } = await api.delete<{ success: boolean; request_id: string }>(
    `/prs/${requestId}`
  );
  return data;
}

export async function getCCRTransactions() {
  const { data } = await api.get<{ items: CCRTransaction[]; total: number }>(
    "/ccr/transactions"
  );
  return data;
}

export async function evaluateCCRTransaction(transactionId: string) {
  const { data } = await api.post<{
    transaction_id: string;
    expected_ccr_decision: string;
    matches_expected: boolean;
    contract_number: string;
    contract_filename: string;
    result: Record<string, unknown>;
  }>(`/ccr/transactions/${transactionId}/evaluate`);
  return data;
}
