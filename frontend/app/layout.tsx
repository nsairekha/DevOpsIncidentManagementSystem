import type { Metadata } from "next";
import "./globals.css";
import AppShell from "../components/AppShell";

export const metadata: Metadata = {
  title: "AI Cloud Observability | Distributed Systems SRE Dashboard",
  description:
    "AI-Based Cloud Observability System for Distributed Systems - Live metrics, anomaly detection, dependency map, and blockchain audit trail.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 antialiased font-sans selection:bg-cyan-500/20 selection:text-cyan-300">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
