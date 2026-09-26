"use client";
import { ReactNode } from "react";
import { Trash2, X } from "lucide-react";
import { DNSRecord, HostedZone } from "@/types/route53";
import { RecordForm, ZoneForm } from "./Forms";

export function EditorModal({ kind, zone, record, busy, onClose, onZone, onRecord }: { kind: "zone" | "record"; zone?: HostedZone; record?: DNSRecord; busy: boolean; onClose: () => void; onZone: Parameters<typeof ZoneForm>[0]["onSubmit"]; onRecord: Parameters<typeof RecordForm>[0]["onSubmit"] }) {
  const title = kind === "zone" ? (zone ? "Edit hosted zone" : "Create hosted zone") : (record ? "Edit record" : "Create record");
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><div className="modal-head"><h2 id="dialog-title">{title}</h2><button onClick={onClose} aria-label="Close" className="icon-button"><X size={20}/></button></div>{kind === "zone" ? <ZoneForm value={zone} busy={busy} onCancel={onClose} onSubmit={onZone}/> : <RecordForm value={record} busy={busy} onCancel={onClose} onSubmit={onRecord}/>}</section></div>;
}
export function ConfirmModal({ title, description, onCancel, onConfirm, busy = false }: { title: string; description: string; onCancel: () => void; onConfirm: () => void; busy?: boolean }) {
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onCancel(); }}><section className="modal confirm-modal" role="alertdialog" aria-modal="true"><div className="modal-head"><h2>{title}</h2><button onClick={onCancel} aria-label="Close" className="icon-button"><X size={20}/></button></div><p className="desc">{description}</p><div className="form-actions"><button className="btn" onClick={onCancel}>Cancel</button><button className="btn danger" disabled={busy} onClick={onConfirm}><Trash2 size={14}/> {busy ? "Deleting…" : "Delete"}</button></div></section></div>;
}
export function Toast({ children, error = false }: { children: ReactNode; error?: boolean }) {
  const role = error ? "alert" : "status";
  return <div className={`toast ${error ? "error" : ""}`} role={role}>{children}</div>;
}
