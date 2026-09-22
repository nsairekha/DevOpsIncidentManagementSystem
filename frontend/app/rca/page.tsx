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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-500" : developerPreview ? "bg-amber-500" : "bg-slate-400"
              }`}
            />
          </span>
          <div className="text-xs">
            <span className="font-semibold text-slate-900">
              {isLive
                ? "Live RCA pipeline"
                : developerPreview
                ? "Demo data (developer preview)"
                : "Backend RCA status"}
            </span>
            <span className="text-slate-500 ml-2">
              Endpoint: <code className="bg-slate-100 text-slate-600 rounded px-1 font-mono">{API_BASE_URL}/api/rca</code>
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
              className="text-[11px] px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 transition-colors"
            >
              {developerPreview ? "Hide Preview" : "Developer UI Preview"}
            </button>
          )}
        </div>
      </div>

      {/* Page Title */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          AI Root Cause Analysis (RCA)
        </h2>
        <p className="text-sm text-slate-500">
          Autonomous failure localization, causal graph deduction, and remediation playbooks
        </p>
      </div>

      {/* When RCA data is NOT available and developer preview is OFF */}
      {!displayRCA && (
        <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-12 text-center space-y-4">
          <div className="inline-flex p-4 rounded-full bg-slate-100 border border-slate-200 text-slate-500">
            <GitPullRequest className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-900">
              RCA data not available
            </h3>
            <p className="text-xs text-slate-500 max-w-lg mx-auto">
              The backend RCA endpoint (<code className="bg-slate-100 text-slate-600 rounded px-1 font-mono">/api/rca</code>) has not yet published an active root cause diagnosis.
              When an incident agent detects failure propagation across the microservices, structured causal evidence will be displayed here.
            </p>
          </div>

          <div className="pt-3">
            <button
              onClick={() => setDeveloperPreview(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-xs text-slate-700 transition-colors"
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
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-700 flex items-center justify-between">
              <span>
                <strong>Demo data:</strong> Displaying development-only RCA schema preview. Live backend RCA is not available.
              </span>
              <button
                onClick={() => setDeveloperPreview(false)}
                className="text-[11px] underline hover:text-amber-800"
              >
                Hide
              </button>
            </div>
          )}

          {/* 1. Incident & Suspected Root Cause Card */}
          <div className="rounded-xl bg-white border border-rose-200 shadow-sm p-6 space-y-4">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-lg bg-rose-50 text-rose-600 border border-rose-100 shrink-0">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold text-slate-900">
                    {displayRCA.incident}
                  </h3>
                  <StatusBadge status="Critical" size="sm" pulse={true} />
                </div>
                <p className="text-xs text-slate-500">
                  Affected service:{" "}
                  <strong className="text-rose-600">
                    {displayRCA.affectedService}
                  </strong>
                </p>
              </div>
            </div>

            {/* Suspected Root Cause Box */}
            <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-xs space-y-1">
              <span className="text-[11px] text-rose-700 font-medium block">
                Suspected root cause:
              </span>
              <p className="text-slate-700 leading-relaxed">
                {displayRCA.suspectedRootCause}
              </p>
            </div>
          </div>

          {/* 2. Evidence & Affected Dependencies Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
            {/* Evidence */}
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-3">
              <span className="text-xs text-slate-600 font-medium block">
                Diagnostic evidence
              </span>
              <ul className="space-y-2">
                {displayRCA.evidence.map((item, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-slate-50 border border-slate-200 flex items-start gap-2 text-slate-700"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Affected Dependencies */}
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-3">
              <span className="text-xs text-slate-600 font-medium block">
                Affected downstream dependencies
              </span>
              <ul className="space-y-2">
                {displayRCA.affectedDependencies.map((dep, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-slate-50 border border-slate-200 flex items-start gap-2 text-slate-700"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <span>{dep}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 3. Timeline */}
          <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-indigo-600" />
              <h3 className="text-sm font-semibold text-slate-900">
                Incident Propagation Timeline
              </h3>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 text-xs">
              {displayRCA.timeline.map((step, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-[23px] top-0.5 w-3 h-3 rounded-full bg-indigo-600 ring-4 ring-indigo-100" />
                  <div className="space-y-0.5">
                    <span className="text-[11px] text-slate-500 font-mono">{step.time}</span>
                    <p className="font-semibold text-slate-900">{step.event}</p>
                    <p className="text-slate-500 text-[11px]">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4. AI Explanation & Recommended Action */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 text-xs">
            {/* AI Explanation */}
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-3">
              <span className="text-xs text-slate-600 font-medium block">
                AI model explanation
              </span>
              <p className="text-slate-700 leading-relaxed p-3.5 rounded bg-slate-50 border border-slate-200">
                {displayRCA.aiExplanation}
              </p>
            </div>

            {/* Recommended Action */}
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-xs text-slate-600 font-medium block mb-2">
                  Recommended remediation action
                </span>
                <p className="text-slate-700 leading-relaxed p-3.5 rounded bg-emerald-50 border border-emerald-200">
                  {displayRCA.recommendedAction}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                <span className="text-[11px] text-slate-500">
                  {remediationApplied ? (
                    <span className="text-emerald-600 flex items-center gap-1 font-medium">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Action Applied
                    </span>
                  ) : (
                    "Operator Action Required"
                  )}
                </span>

                <button
                  onClick={() => setRemediationApplied(true)}
                  disabled={remediationApplied}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    remediationApplied
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : "bg-indigo-600 hover:bg-indigo-700 text-white"
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
