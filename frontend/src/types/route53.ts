export const RECORD_TYPES = ["A", "AAAA", "CNAME", "TXT", "MX", "NS", "PTR", "SRV", "CAA", "SOA"] as const;
export type RecordType = (typeof RECORD_TYPES)[number];
export type HostedZone = { id: number; name: string; comment: string; is_private: boolean; created_at: string; record_count: number };
export type DNSRecord = { id: number; zone_id: number; name: string; type: RecordType; value: string; ttl: number; routing_policy: string; created_at: string };
export type PageData<T> = { items: T[]; total: number; page: number; page_size: number };
export type ZonePayload = Pick<HostedZone, "name" | "comment" | "is_private">;
export type RecordPayload = Pick<DNSRecord, "name" | "type" | "value" | "ttl" | "routing_policy">;
