import type { DNSRecord, HostedZone, PageData, RecordPayload, ZonePayload } from "@/types/route53";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); message = typeof body.detail === "string" ? body.detail : body.detail?.[0]?.msg || message; } catch { /* use status text */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const getZones = (search: string, page: number) => request<PageData<HostedZone>>(`/zones?search=${encodeURIComponent(search)}&page=${page}&page_size=8`);
export const getRecords = (zoneId: number, search: string, type: string, page: number) => request<PageData<DNSRecord>>(`/zones/${zoneId}/records?search=${encodeURIComponent(search)}&record_type=${encodeURIComponent(type)}&page=${page}&page_size=8`);
export const saveZone = (payload: ZonePayload, id?: number) => request<HostedZone>(id ? `/zones/${id}` : "/zones", { method: id ? "PATCH" : "POST", body: JSON.stringify(payload) });
export const deleteZone = (id: number) => request<void>(`/zones/${id}`, { method: "DELETE" });
export const saveRecord = (payload: RecordPayload, zoneId: number, id?: number) => request<DNSRecord>(id ? `/records/${id}` : `/zones/${zoneId}/records`, { method: id ? "PATCH" : "POST", body: JSON.stringify(payload) });
export const deleteRecord = (id: number) => request<void>(`/records/${id}`, { method: "DELETE" });
export const getZone = (id: number) => request<HostedZone>(`/zones/${id}`);
export const getSummary = () => request<{ hosted_zones: number; dns_records: number }>("/summary");
export const importZoneFile = (zoneId: number, content: string) => request<{ imported: number; skipped: string[] }>(`/zones/${zoneId}/import`, { method: "POST", body: JSON.stringify({ content }) });
export const bulkDeleteZones = (ids: number[]) => request<{ deleted: number; not_found: number[] }>("/zones/bulk-delete", { method: "POST", body: JSON.stringify({ ids }) });
export const bulkDeleteRecords = (ids: number[]) => request<{ deleted: number; not_found: number[] }>("/records/bulk-delete", { method: "POST", body: JSON.stringify({ ids }) });
