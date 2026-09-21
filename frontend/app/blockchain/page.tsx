"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Blocks,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Search,
  CheckCircle2,
  Copy,
  Check,
  ShieldAlert,
  Fingerprint,
} from "lucide-react";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState } from "../../components/LoadingState";
import {
  API_BASE_URL,
  AuditResponse,
  fetchAuditTrail,
  verifyAuditChain,
} from "../../lib/api";

export default function BlockchainAuditPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const [isLive, setIsLive] = useState(false);
  const [auditData, setAuditData] = useState<AuditResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Verification button state
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    valid: boolean;
    timestamp: string;
    message: string;
  } | null>(null);

  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const loadAudit = useCallback(async () => {
    try {
      setRefreshing(true);
      const res = await fetchAuditTrail();

      if (res.isLive && res.data) {
        setIsLive(true);
        setAuditData(res.data);
        setStatusMessage(null);
      } else {
        setIsLive(false);
        setAuditData(null);
        setStatusMessage("Blockchain audit integration not available.");
      }
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAudit();
  }, [loadAudit]);

  const handleVerifyRecord = async () => {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await verifyAuditChain();
      setVerifyResult({
        valid: result.valid,
        timestamp: new Date().toLocaleTimeString(),
        message: result.isLive
          ? `Verification complete: ${result.length} blocks verified cryptographically. Status: ${
              result.valid ? "VALID & UNBROKEN" : "INTEGRITY VIOLATED"
            }`
          : "Blockchain audit integration not available.",
      });
      await loadAudit();
    } finally {
      setVerifying(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 1500);
  };

  if (loading && !auditData && !statusMessage) {
    return (
      <LoadingState
        type="full"
        message="Verifying cryptographic blockchain ledger..."
      />
    );
  }

  const blocks = auditData?.blocks || [];
  const filteredBlocks = blocks.filter(
    (b) =>
      b.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.hash.toLowerCase().includes(searchTerm.toLowerCase()) ||
      b.index.toString() === searchTerm
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg bg-surface border border-border">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-400" : "bg-slate-500"
              }`}
            />
          </span>
          <div className="text-xs font-mono">
            <span className="font-bold text-white uppercase tracking-wide">
              {isLive ? "LIVE BLOCKCHAIN INTEGRATION" : "BLOCKCHAIN INTEGRATION OFFLINE"}
            </span>
            <span className="text-slate-400 ml-2">
              Endpoint: <code>{API_BASE_URL}/api/audit</code>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadAudit}
            intervalSeconds={10}
            isRefreshing={refreshing}
          />
        </div>
      </div>

      {/* Page Title & Verify Record Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Blockchain Audit Trail & Proof-of-Telemetry
          </h2>
          <p className="text-xs font-mono text-slate-400">
            Append-only verifiable cryptographic ledger securing incident detections and automated remediation
          </p>
        </div>

        {/* VERIFY RECORD BUTTON (Requirement 10) */}
        <button
          onClick={handleVerifyRecord}
          disabled={verifying}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all shadow-lg shadow-cyan-950/40 disabled:opacity-60 self-start sm:self-auto"
        >
          <Fingerprint
            className={`h-4 w-4 ${verifying ? "animate-spin text-cyan-200" : ""}`}
          />
          <span>{verifying ? "Verifying Proofs..." : "Verify Record"}</span>
        </button>
      </div>

      {/* Verification Result Toast/Banner */}
      {verifyResult && (
        <div
          className={`p-4 rounded-lg border font-mono text-xs flex items-center justify-between animate-in fade-in-50 duration-200 ${
            verifyResult.valid
              ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
              : "bg-rose-950/40 border-rose-800 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2.5">
            {verifyResult.valid ? (
              <ShieldCheck className="h-5 w-5 text-emerald-400 shrink-0" />
            ) : (
              <ShieldAlert className="h-5 w-5 text-rose-400 shrink-0" />
            )}
            <span>{verifyResult.message}</span>
          </div>
          <span className="text-[10px] text-slate-400">{verifyResult.timestamp}</span>
        </div>
      )}

      {/* When Blockchain integration is NOT available */}
      {!isLive && (
        <div className="rounded-lg bg-surface border border-border p-12 text-center space-y-4">
          <div className="inline-flex p-4 rounded-full bg-slate-800/80 border border-slate-700 text-slate-400">
            <Blocks className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">
              Blockchain audit integration not available.
            </h3>
            <p className="text-xs font-mono text-slate-400 max-w-lg mx-auto">
              Could not retrieve audit ledger records from{" "}
              <code>{API_BASE_URL}/api/audit</code>. Ensure the backend FastAPI service is running.
            </p>
          </div>

          <div className="pt-2">
            <button
              onClick={loadAudit}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 border border-slate-600 transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Ledger Connection</span>
            </button>
          </div>
        </div>
      )}

      {/* When Blockchain integration IS available (Real backend data) */}
      {isLive && auditData && (
        <div className="space-y-6">
          {/* Integrity KPIs: Incident ID / Verification status / Block count */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
            {/* 1. Verification Status */}
            <div
              className={`rounded-lg bg-surface border p-4 flex items-center justify-between ${
                auditData.valid
                  ? "border-emerald-800/80 shadow-[0_0_15px_-3px_rgba(16,185,129,0.15)]"
                  : "border-rose-800/80 shadow-[0_0_15px_-3px_rgba(239,68,68,0.2)]"
              }`}
            >
              <div>
                <span className="text-[10px] uppercase text-slate-400 block font-semibold">
                  VERIFICATION STATUS
                </span>
                <span
                  className={`text-lg font-bold mt-1 block ${
                    auditData.valid ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {auditData.valid ? "VALID & UNTAMPERED" : "TAMPER DETECTED"}
                </span>
              </div>
              <div
                className={`p-2.5 rounded-lg ${
                  auditData.valid
                    ? "bg-emerald-950 text-emerald-400"
                    : "bg-rose-950 text-rose-400"
                }`}
              >
                {auditData.valid ? (
                  <ShieldCheck className="h-6 w-6" />
                ) : (
                  <AlertTriangle className="h-6 w-6" />
                )}
              </div>
            </div>

            {/* 2. Block Number / Total Blocks */}
            <div className="rounded-lg bg-surface border border-border p-4 flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase text-slate-400 block font-semibold">
                  TOTAL AUDITED BLOCKS
                </span>
                <span className="text-3xl font-bold text-white mt-1 block">
                  {auditData.length}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800 text-cyan-400">
                <Blocks className="h-6 w-6" />
              </div>
            </div>

            {/* 3. Latest Hash */}
            <div className="rounded-lg bg-surface border border-border p-4 flex flex-col justify-between">
              <div>
                <span className="text-[10px] uppercase text-slate-400 block font-semibold">
                  LATEST HEAD HASH
                </span>
                <code className="text-xs text-cyan-400 font-bold break-all block mt-1">
                  {auditData.last_hash
                    ? `${auditData.last_hash.slice(0, 24)}...`
                    : "N/A"}
                </code>
              </div>
              <span className="text-[10px] text-slate-500 mt-2">
                SHA-256 Merkle Chaining
              </span>
            </div>
          </div>

          {/* Block Table:
              Required columns by prompt:
              Incident ID, Hash, Timestamp, Transaction ID, Block number, Verification status */}
          <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Blocks className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">
                  Cryptographic Ledger Explorer ({blocks.length} Blocks)
                </h3>
              </div>

              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search by event or hash..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 pr-3 py-1.5 bg-surface-subtle border border-border rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-48 sm:w-64"
                />
              </div>
            </div>

            <div className="overflow-x-auto border border-border/80 rounded-md bg-surface-subtle">
              <table className="w-full text-left text-xs border-collapse min-w-[760px]">
                <thead>
                  <tr className="border-b border-border bg-slate-900/60 font-mono text-[11px] text-slate-400">
                    <th className="py-2.5 px-3 font-semibold">Block #</th>
                    <th className="py-2.5 px-3 font-semibold">Incident / Event ID</th>
                    <th className="py-2.5 px-3 font-semibold">Transaction Hash</th>
                    <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                    <th className="py-2.5 px-3 font-semibold">Previous Hash</th>
                    <th className="py-2.5 px-3 font-semibold">Verification Status</th>
                    <th className="py-2.5 px-3 text-right">Copy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50 font-mono">
                  {filteredBlocks.map((b) => (
                    <tr
                      key={b.index}
                      className="hover:bg-surface-hover/70 transition-colors"
                    >
                      <td className="py-3 px-3 font-bold text-cyan-400">
                        #{b.index}
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50 text-[11px] font-semibold">
                          {b.event_type || "TELEMETRY_EVENT"}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <code className="text-slate-200 text-[11px]">
                          {b.hash.slice(0, 16)}...
                        </code>
                      </td>

                      <td className="py-3 px-3 text-[11px] text-slate-400">
                        {b.timestamp}
                      </td>

                      <td className="py-3 px-3">
                        <code className="text-slate-500 text-[11px]">
                          {b.previous_hash.slice(0, 14)}...
                        </code>
                      </td>

                      <td className="py-3 px-3">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Chained & Verified</span>
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => copyToClipboard(b.hash)}
                          className="p-1 rounded text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors inline-flex items-center gap-1"
                          title="Copy full cryptographic hash"
                        >
                          {copiedHash === b.hash ? (
                            <Check className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
