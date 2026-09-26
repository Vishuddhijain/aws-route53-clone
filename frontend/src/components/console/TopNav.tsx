// "use client";
// import { Bell, CircleHelp, LogOut, Menu } from "lucide-react";
// import Link from "next/link";
// export function TopNav({ user, onLogout, onMenu }: { user: string; onLogout: () => void; onMenu: () => void }) {
//   return <><header className="topbar"><div className="navleft"><button className="mobile-menu" onClick={onMenu} aria-label="Toggle navigation"><Menu size={20}/></button><Link href="/" className="brand">aws <b>route 53</b></Link><input className="global-search" placeholder="Search AWS services" aria-label="Search AWS services"/></div><div className="navright"><span className="region">Global</span><CircleHelp size={17}/><Bell size={17}/><button className="account-button" onClick={onLogout} title="Sign out"><span>{user}</span><LogOut size={16}/></button></div></header><div className="subbar"><span>Services　›　Networking &amp; Content Delivery　›　Amazon Route 53</span><span>Global</span></div></>;
// }



"use client";
import { Bell, CircleHelp, LogOut, Menu, Moon, Sun } from "lucide-react";
import Link from "next/link";
export function TopNav({ user, dark, onLogout, onMenu, onToggleTheme }: { user: string; dark: boolean; onLogout: () => void; onMenu: () => void; onToggleTheme: () => void }) {
  return <><header className="topbar"><div className="navleft"><button className="mobile-menu" onClick={onMenu} aria-label="Toggle navigation"><Menu size={20}/></button><Link href="/" className="brand">aws <b>route 53</b></Link><input className="global-search" placeholder="Search AWS services" aria-label="Search AWS services"/></div><div className="navright"><button className="theme-toggle" onClick={onToggleTheme} title={dark ? "Switch to light mode" : "Switch to dark mode"} aria-label="Toggle color theme">{dark ? <Sun size={14}/> : <Moon size={14}/>}{dark ? "Light" : "Dark"}</button><span className="region">Global</span><CircleHelp size={17}/><Bell size={17}/><button className="account-button" onClick={onLogout} title="Sign out"><span>{user}</span><LogOut size={16}/></button></div></header><div className="subbar"><span>Services　›　Networking &amp; Content Delivery　›　Amazon Route 53</span><span>Global</span></div></>;
}
