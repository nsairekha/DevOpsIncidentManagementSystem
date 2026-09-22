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
    <html lang="en">
      <body className="bg-[#F6F7F9] text-slate-900 antialiased font-sans selection:bg-indigo-100 selection:text-indigo-900">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
