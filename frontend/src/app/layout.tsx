// import type { Metadata } from "next";
// import "./globals.css";
// export const metadata: Metadata = { title: "Amazon Route 53 | AWS Console", description: "Manage hosted zones and DNS records" };
// export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }


import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { ThemeProvider } from "@/components/console/ThemeProvider";

export const metadata: Metadata = {
  title: "Amazon Route 53 | AWS Console",
  description: "Manage hosted zones and DNS records",
};

// Runs before hydration (Next.js "beforeInteractive" strategy injects this
// into <head> and executes it before any page JS, including React itself).
// Reading localStorage and setting data-theme here — rather than in a
// useEffect after mount — is what prevents a flash of the wrong theme on
// first load and on every hard refresh.
const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem("route53-theme");
    var theme = stored || (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {
    // localStorage unavailable — fall back to the default light theme
  }
})();
`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    // suppressHydrationWarning is required here because the theme-init script
    // below sets data-theme on <html> directly (before React hydrates), so
    // the attribute React sees on mount won't match what it rendered on the
    // server. React only skips the mismatch check for this one element's
    // attributes — it does not suppress warnings for anything inside <body>.
    <html lang="en" suppressHydrationWarning>
      <body>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInitScript}
        </Script>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
