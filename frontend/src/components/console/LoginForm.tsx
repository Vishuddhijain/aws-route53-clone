"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
export function LoginForm({ onLogin }: { onLogin: (email: string) => void }) {
  const [email, setEmail] = useState("demo@route53.local"); const [error, setError] = useState(""); const router = useRouter();
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); try { localStorage.setItem("route53-session", JSON.stringify({ user: email, at: Date.now() })); onLogin(email); router.push("/"); } catch { setError("This browser could not save your demo session."); } }
  return <main className="login"><form className="login-card" onSubmit={submit}><div className="brand login-brand">amazon <b>route 53</b></div><h1 className="login-title">Sign in to AWS</h1><p className="desc">Sign in to continue to the Route 53 console demo.</p><div className="formrow login-field"><label htmlFor="login-email">Email address</label><input id="login-email" className="field" type="email" required autoComplete="username" value={email} onChange={e => setEmail(e.target.value)}/></div><div className="formrow"><label htmlFor="login-password">Password</label><input id="login-password" className="field" type="password" required autoComplete="current-password" defaultValue="route53-demo"/></div>{error && <p className="inline-error">{error}</p>}<button className="btn primary login-submit">Sign in</button><p className="muted small">Mock authentication. Any valid email and non-empty password work.</p></form></main>;
}
