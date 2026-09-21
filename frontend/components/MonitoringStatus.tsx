import React from "react";
import { Cloud, Activity, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { MonitoringSourcesData } from "../lib/types";

interface MonitoringStatusProps {
  data: MonitoringSourcesData;
  isDemo?: boolean;
}

export default function MonitoringStatus({
  data,
  isDemo = false,
}: MonitoringStatusProps) {
  const { prometheus, cloudwatch } = data;

  return (
    <div className="rounded-lg bg-surface border border-border p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-200 tracking-tight">
              Monitoring Infrastructure
            </h3>
            {isDemo && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950/50 text-amber-400 border border-amber-800/50">
                Demo
              </span>
            )}
          </div>
          <p className="text-[11px] font-mono text-slate-400">
            Active metric ingestion pipelines
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Prometheus Card */}
        <div className="rounded-lg bg-surface-subtle border border-border/80 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-md bg-orange-950/60 text-orange-400 border border-orange-800/40">
                <Activity className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Prometheus</h4>
                <p className="text-[10px] font-mono text-slate-400">
                  {prometheus.url || "http://localhost:9090"}
                </p>
              </div>
            </div>
            <StatusBadge
              status={prometheus.status}
              size="sm"
              pulse={prometheus.status === "Connected"}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50 text-xs font-mono">
            <div className="bg-surface p-2 rounded border border-border/40">
              <span className="text-[10px] text-slate-400 uppercase block">
                Total Targets
              </span>
              <span className="text-sm font-bold text-slate-200">
                {prometheus.targetCount} Scrape Jobs
              </span>
            </div>

            <div className="bg-surface p-2 rounded border border-border/40">
              <span className="text-[10px] text-slate-400 uppercase block">
                Healthy Targets
              </span>
              <span
                className={`text-sm font-bold ${
                  prometheus.healthyTargets === prometheus.targetCount
                    ? "text-emerald-400"
                    : "text-amber-400"
                }`}
              >
                {prometheus.healthyTargets} / {prometheus.targetCount}
              </span>
            </div>
          </div>
        </div>

        {/* CloudWatch Card */}
        <div className="rounded-lg bg-surface-subtle border border-border/80 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-md bg-sky-950/60 text-sky-400 border border-sky-800/40">
                <Cloud className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">AWS CloudWatch</h4>
                <p className="text-[10px] font-mono text-slate-400">
                  {cloudwatch.region} • {cloudwatch.namespace || "AWS Metrics"}
                </p>
              </div>
            </div>
            <StatusBadge
              status={cloudwatch.status}
              size="sm"
              pulse={cloudwatch.status === "Connected"}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50 text-xs font-mono">
            <div className="bg-surface p-2 rounded border border-border/40">
              <span className="text-[10px] text-slate-400 uppercase block">
                AWS Region
              </span>
              <span className="text-sm font-bold text-slate-200">
                {cloudwatch.region}
              </span>
            </div>

            <div className="bg-surface p-2 rounded border border-border/40">
              <span className="text-[10px] text-slate-400 uppercase block">
                Availability
              </span>
              <span
                className={`text-sm font-bold ${
                  cloudwatch.available ? "text-emerald-400" : "text-slate-400"
                }`}
              >
                {cloudwatch.available ? "Available" : "Disabled"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
