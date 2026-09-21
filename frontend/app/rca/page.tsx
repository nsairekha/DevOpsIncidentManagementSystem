"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  GitPullRequest,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Terminal,
  Zap,
  CheckCircle2,
  Info,
  Check,
} from "lucide-react";
import StatusBadge from "../../components/StatusBadge";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState } from "../../components/LoadingState";
import { API_BASE_URL, fetchRCAData } from "../../lib/api";
import { DEMO_RCA, DemoRCA } from "../../lib/demoData";

export default function RootCauseAnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Live vs Fallback state
  const [isLive, setIsLive] = useState(false);
  const [rcaData, setRcaData] = useState<DemoRCA | null>(null);
  const [rcaMessage, setRcaMessage] = useState<string>("Checking backend RCA endpoint...");
  const [developerPreview, setDeveloperPreview] = useState(false);
  const [remediationApplied, setRemediationApplied] = useState(false);

  const loadRCA = useCallback(async () => {
    try {
      setRefreshing(true);
      const res = await fetchRCAData();

      if (res.available && res.data) {
        setIsLive(true);
        setRcaData(res.data);
        setRcaMessage(res.message);
      } else {
        setIsLive(false);
        setRcaData(null);
        setRcaMessage("RCA data not available");
      }
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadRCA();
  }, [loadRCA]);

  if (loading) {
    return <LoadingState type="full" message="Connecting to incident RCA pipeline..." />;
  }

  // Active display data (either live or developer preview)
  const displayRCA = rcaData || (developerPreview ? DEMO_RCA : null);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg bg-surface border border-border">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-400" : developerPreview ? "bg-amber-400" : "bg-slate-500"
              }`}
            />
          </span>
          <div className="text-xs font-mono">
            <span className="font-bold text-white uppercase tracking-wide">
              {isLive
                ? "LIVE RCA PIPELINE"
                : developerPreview
                ? "DEMO DATA (Developer Preview)"
                : "BACKEND RCA STATUS"}
            </span>
            <span className="text-slate-400 ml-2">
              Endpoint: <code>{API_BASE_URL}/api/rca</code>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadRCA}
            intervalSeconds={10}
            isRefreshing={refreshing}
          />

          {!isLive && (
            <button
              onClick={() => setDeveloperPreview(!developerPreview)}
              className="text-[11px] font-mono px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              {developerPreview ? "Hide Preview" : "Developer UI Preview"}
            </button>
          )}
        </div>
      </div>

      {/* Page Title */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          AI Root Cause Analysis (RCA)
        </h2>
        <p className="text-xs font-mono text-slate-400">
          Autonomous failure localization, causal graph deduction, and remediation playbooks
        </p>
      </div>

      {/* When RCA data is NOT available and developer preview is OFF */}
      {!displayRCA && (
        <div className="rounded-lg bg-surface border border-border p-12 text-center space-y-4">
          <div className="inline-flex p-4 rounded-full bg-slate-800/80 border border-slate-700 text-slate-400">
            <GitPullRequest className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">
              RCA data not available
            </h3>
            <p className="text-xs font-mono text-slate-400 max-w-lg mx-auto">
              The backend RCA endpoint (<code className="text-cyan-400">/api/rca</code>) has not yet published an active root cause diagnosis.
              When an incident agent detects failure propagation across the microservices, structured causal evidence will be displayed here.
            </p>
          </div>

          <div className="pt-3">
            <button
              onClick={() => setDeveloperPreview(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 border border-slate-600 transition-colors"
            >
              <span>Enable Developer UI Preview</span>
            </button>
          </div>
        </div>
      )}

      {/* When RCA data is available (Live or Developer Preview) */}
      {displayRCA && (
        <div className="space-y-6">
          {developerPreview && !isLive && (
            <div className="rounded-lg border border-amber-800/70 bg-amber-950/30 px-4 py-2 text-xs font-mono text-amber-300 flex items-center justify-between">
              <span>
                <strong>DEMO DATA:</strong> Displaying development-only RCA schema preview. Live backend RCA is not available.
              </span>
              <button
                onClick={() => setDeveloperPreview(false)}
                className="text-[11px] underline hover:text-amber-100"
              >
                Hide
              </button>
            </div>
          )}

          {/* 1. Incident & Suspected Root Cause Card */}
          <div className="rounded-lg bg-surface border border-rose-800/70 p-6 shadow-[0_0_20px_-3px_rgba(239,68,68,0.15)] space-y-4">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-lg bg-rose-950/80 text-rose-400 border border-rose-800 shrink-0">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white">
                    {displayRCA.incident}
                  </h3>
                  <StatusBadge status="Critical" size="sm" pulse={true} />
                </div>
                <p className="text-xs text-slate-300 font-mono">
                  Affected Service:{" "}
                  <strong className="text-rose-400">
                    {displayRCA.affectedService}
                  </strong>
                </p>
              </div>
            </div>

            {/* Suspected Root Cause Box */}
            <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-800/60 font-mono text-xs space-y-1">
              <span className="text-[10px] text-rose-400 uppercase font-bold block">
                SUSPECTED ROOT CAUSE:
              </span>
              <p className="text-slate-200 font-sans leading-relaxed">
                {displayRCA.suspectedRootCause}
              </p>
            </div>
          </div>

          {/* 2. Evidence & Affected Dependencies Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 font-mono text-xs">
            {/* Evidence */}
            <div className="rounded-lg bg-surface border border-border p-5 space-y-3">
              <span className="text-[10px] uppercase text-cyan-400 font-bold tracking-wider block">
                DIAGNOSTIC EVIDENCE
              </span>
              <ul className="space-y-2">
                {displayRCA.evidence.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-surface-subtle border border-border/70 flex items-start gap-2 text-slate-300"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Affected Dependencies */}
            <div className="rounded-lg bg-surface border border-border p-5 space-y-3">
              <span className="text-[10px] uppercase text-amber-400 font-bold tracking-wider block">
                AFFECTED DOWNSTREAM DEPENDENCIES
              </span>
              <ul className="space-y-2">
                {displayRCA.affectedDependencies.map((dep, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-surface-subtle border border-border/70 flex items-start gap-2 text-slate-300"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span>{dep}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 3. Timeline */}
          <div className="rounded-lg bg-surface border border-border p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">
                Incident Propagation Timeline
              </h3>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border font-mono text-xs">
              {displayRCA.timeline.map((step, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-[23px] top-0.5 w-3 h-3 rounded-full bg-cyan-500 ring-4 ring-cyan-950" />
                  <div className="space-y-0.5">
                    <span className="text-[10px] text-slate-400">{step.time}</span>
                    <p className="font-bold text-white">{step.event}</p>
                    <p className="text-slate-400 text-[11px]">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4. AI Explanation & Recommended Action */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 font-mono text-xs">
            {/* AI Explanation */}
            <div className="rounded-lg bg-surface border border-border p-5 space-y-3">
              <span className="text-[10px] uppercase text-indigo-400 font-bold tracking-wider block">
                AI MODEL EXPLANATION
              </span>
              <p className="text-slate-300 font-sans leading-relaxed p-3.5 rounded bg-surface-subtle border border-border/60">
                {displayRCA.aiExplanation}
              </p>
            </div>

            {/* Recommended Action */}
            <div className="rounded-lg bg-surface border border-border p-5 space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-[10px] uppercase text-emerald-400 font-bold tracking-wider block mb-2">
                  RECOMMENDED REMEDIATION ACTION
                </span>
                <p className="text-slate-200 font-sans leading-relaxed p-3.5 rounded bg-emerald-950/20 border border-emerald-800/50">
                  {displayRCA.recommendedAction}
                </p>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {remediationApplied ? (
                    <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Action Applied
                    </span>
                  ) : (
                    "Operator Action Required"
                  )}
                </span>

                <button
                  onClick={() => setRemediationApplied(true)}
                  disabled={remediationApplied}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    remediationApplied
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      : "bg-cyan-600 hover:bg-cyan-500 text-white"
                  }`}
                >
                  {remediationApplied ? (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      <span>Executed</span>
                    </>
                  ) : (
                    <>
                      <Zap className="h-3.5 w-3.5 fill-current" />
                      <span>Execute Remediation</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
