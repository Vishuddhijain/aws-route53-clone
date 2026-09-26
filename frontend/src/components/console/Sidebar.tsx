"use client";
import Link from "next/link";
import { Activity, Boxes, Cloud, Globe2, LayoutDashboard, Network } from "lucide-react";
const nav = [{ href: "/", label: "Dashboard", icon: LayoutDashboard }, { href: "/hosted-zones", label: "Hosted zones", icon: Globe2 }];
const features = [{ href: "/traffic-policies", label: "Traffic policies", icon: Network }, { href: "/health-checks", label: "Health checks", icon: Activity }, { href: "/resolver", label: "Resolver", icon: Cloud }, { href: "/profiles", label: "Profiles", icon: Boxes }];
export function Sidebar({ path, open, close }: { path: string; open: boolean; close: () => void }) {
  const active = (href: string) => path === href || (href === "/hosted-zones" && path.startsWith(href));
  return <aside className={`sidebar ${open ? "open" : ""}`}><div className="side-title">Amazon Route 53</div>{nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={close} className={`side-link ${active(href) ? "active" : ""}`}><Icon size={16}/>{label}</Link>)}<div className="side-title side-heading">ROUTING FEATURES</div>{features.map(({ href, label, icon: Icon }) => <Link key={href} href={href} onClick={close} className={`side-link ${active(href) ? "active" : ""}`}><Icon size={16}/>{label}</Link>)}</aside>;
}
