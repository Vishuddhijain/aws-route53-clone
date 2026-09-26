"use client";
import { ArrowLeft, ArrowRight } from "lucide-react";
export function Pagination({ page, total, onChange, pageSize = 8 }: { page: number; total: number; onChange: (page: number) => void; pageSize?: number }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return <div className="pagination"><span>{total ? `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}` : "0 results"}</span><div className="page-controls"><button className="btn" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Previous page"><ArrowLeft size={15}/></button><span>Page {page} of {pages}</span><button className="btn" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Next page"><ArrowRight size={15}/></button></div></div>;
}
