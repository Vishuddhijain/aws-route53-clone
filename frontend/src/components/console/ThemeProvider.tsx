"use client";

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";

const STORAGE_KEY = "route53-theme";

interface ThemeContextValue {
  dark: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * Global theme provider — mounted once in the root layout, so it survives
 * client-side navigation between routes (unlike page-level state, which
 * Next.js remounts on every route change).
 *
 * The actual `data-theme` attribute on <html> is set synchronously by a
 * beforeInteractive script in layout.tsx, before React hydrates, so there
 * is no flash of the wrong theme on first load or refresh. This provider's
 * initial state just reads that already-correct attribute back out, and
 * takes over from there.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(
    () => typeof document !== "undefined" && document.documentElement.getAttribute("data-theme") === "dark"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    try {
      localStorage.setItem(STORAGE_KEY, dark ? "dark" : "light");
    } catch {
      // storage unavailable — theme still applies for this session
    }
  }, [dark]);

  const toggleTheme = useCallback(() => setDark((value) => !value), []);

  return <ThemeContext.Provider value={{ dark, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}
