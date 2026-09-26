"use client";
import Link from "next/link";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";
export function Layout({ children, path, title, user, dark, menuOpen, onMenu, onLogout, onToggleTheme }: { children: React.ReactNode; path: string; title: string; user: string; dark: boolean; menuOpen: boolean; onMenu: () => void; onLogout: () => void; onToggleTheme: () => void }) {
  return <div className="shell"><TopNav user={user} dark={dark} onLogout={onLogout} onMenu={onMenu} onToggleTheme={onToggleTheme}/><div className="layout"><Sidebar path={path} open={menuOpen} close={onMenu}/><main className="main"><div className="crumb"><Link href="/">Route 53</Link>{path !== "/" && <>　›　{path.startsWith("/hosted-zones/") ? <><Link href="/hosted-zones">Hosted zones</Link>　›　{title}</> : title}</>}</div>{children}<div className="footer">© 2026, Amazon Web Services, Inc. or its affiliates. Console demonstration project.</div></main></div></div>;
}
