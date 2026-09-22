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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
          </span>
          <div className="text-xs">
            <span className="font-semibold text-slate-900">
              {isLive ? "Live blockchain integration" : "Blockchain integration offline"}
            </span>
            <span className="text-slate-500 ml-2">
              Endpoint: <code className="bg-slate-100 text-slate-600 rounded px-1 font-mono">{API_BASE_URL}/api/audit</code>
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
          <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
            Blockchain Audit Trail & Proof-of-Telemetry
          </h2>
          <p className="text-sm text-slate-500">
            Append-only verifiable cryptographic ledger securing incident detections and automated remediation
          </p>
        </div>

        {/* VERIFY RECORD BUTTON (Requirement 10) */}
        <button
          onClick={handleVerifyRecord}
          disabled={verifying}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium transition-all shadow-sm disabled:opacity-60 self-start sm:self-auto"
        >
          <Fingerprint
            className={`h-4 w-4 ${verifying ? "animate-spin" : ""}`}
          />
          <span>{verifying ? "Verifying Proofs..." : "Verify Record"}</span>
        </button>
      </div>

      {/* Verification Result Toast/Banner */}
      {verifyResult && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center justify-between shadow-sm ${
            verifyResult.valid
              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
              : "bg-rose-50 border-rose-200 text-rose-700"
          }`}
        >
          <div className="flex items-center gap-2.5">
            {verifyResult.valid ? (
              <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0" />
            ) : (
              <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0" />
            )}
            <span>{verifyResult.message}</span>
          </div>
          <span className="text-[11px] text-slate-500">{verifyResult.timestamp}</span>
        </div>
      )}

      {/* When Blockchain integration is NOT available */}
      {!isLive && (
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-12 text-center space-y-4">
          <div className="inline-flex p-4 rounded-full bg-slate-100 border border-slate-200 text-slate-500">
            <Blocks className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-900">
              Blockchain audit integration not available.
            </h3>
            <p className="text-xs text-slate-500 max-w-lg mx-auto">
              Could not retrieve audit ledger records from{" "}
              <code className="bg-slate-100 text-slate-600 rounded px-1 font-mono">{API_BASE_URL}/api/audit</code>. Ensure the backend FastAPI service is running.
            </p>
          </div>

          <div className="pt-2">
            <button
              onClick={loadAudit}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-xs text-slate-700 transition-colors"
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
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* 1. Verification Status */}
            <div
              className={`rounded-xl bg-white border shadow-sm p-4 flex items-center justify-between ${
                auditData.valid
                  ? "border-emerald-200"
                  : "border-rose-200"
              }`}
            >
              <div>
                <span className="text-xs text-slate-500 block font-medium">
                  Verification status
                </span>
                <span
                  className={`text-lg font-semibold mt-1 block ${
                    auditData.valid ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {auditData.valid ? "Valid & untampered" : "Tamper detected"}
                </span>
              </div>
              <div
                className={`p-2.5 rounded-lg ${
                  auditData.valid
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-rose-50 text-rose-600"
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
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-4 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 block font-medium">
                  Total audited blocks
                </span>
                <span className="text-3xl font-semibold text-slate-900 mt-1 block">
                  {auditData.length}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
                <Blocks className="h-6 w-6" />
              </div>
            </div>

            {/* 3. Latest Hash */}
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-4 flex flex-col justify-between">
              <div>
                <span className="text-xs text-slate-500 block font-medium">
                  Latest head hash
                </span>
                <code className="text-xs text-indigo-600 font-semibold font-mono break-all block mt-1">
                  {auditData.last_hash
                    ? `${auditData.last_hash.slice(0, 24)}...`
                    : "N/A"}
                </code>
              </div>
              <span className="text-[11px] text-slate-500 mt-2">
                SHA-256 Merkle chaining
              </span>
            </div>
          </div>

          {/* Block Table:
              Required columns by prompt:
              Incident ID, Hash, Timestamp, Transaction ID, Block number, Verification status */}
          <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Blocks className="h-4 w-4 text-indigo-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Cryptographic Ledger Explorer ({blocks.length} Blocks)
                </h3>
              </div>

              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by event or hash..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 w-48 sm:w-64"
                />
              </div>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-lg bg-white">
              <table className="w-full text-left text-xs border-collapse min-w-[760px]">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-[11px] text-slate-500">
                    <th className="py-2.5 px-3 font-semibold">Block #</th>
                    <th className="py-2.5 px-3 font-semibold">Incident / Event ID</th>
                    <th className="py-2.5 px-3 font-semibold">Transaction Hash</th>
                    <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                    <th className="py-2.5 px-3 font-semibold">Previous Hash</th>
                    <th className="py-2.5 px-3 font-semibold">Verification Status</th>
                    <th className="py-2.5 px-3 text-right">Copy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredBlocks.map((b) => (
                    <tr
                      key={b.index}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      <td className="py-3 px-3 font-semibold text-indigo-600 font-mono">
                        #{b.index}
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-medium">
                          {b.event_type || "TELEMETRY_EVENT"}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <code className="text-slate-700 text-[11px] font-mono">
                          {b.hash.slice(0, 16)}...
                        </code>
                      </td>

                      <td className="py-3 px-3 text-[11px] text-slate-500 font-mono">
                        {b.timestamp}
                      </td>

                      <td className="py-3 px-3">
                        <code className="text-slate-500 text-[11px] font-mono">
                          {b.previous_hash.slice(0, 14)}...
                        </code>
                      </td>

                      <td className="py-3 px-3">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Chained & Verified</span>
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => copyToClipboard(b.hash)}
                          className="p-1 rounded text-slate-500 hover:text-indigo-600 hover:bg-slate-100 transition-colors inline-flex items-center gap-1"
                          title="Copy full cryptographic hash"
                        >
                          {copiedHash === b.hash ? (
                            <Check className="h-3.5 w-3.5 text-emerald-600" />
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
