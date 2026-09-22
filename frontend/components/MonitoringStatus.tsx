import React from "react";
import { Cloud, Activity } from "lucide-react";
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
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Monitoring Infrastructure
            </h3>
            {isDemo && (
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                Demo
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500">
            Active metric ingestion pipelines
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Prometheus Card */}
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-md bg-orange-50 text-orange-600 border border-orange-100">
                <Activity className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">Prometheus</h4>
                <p className="text-[10px] text-slate-500">
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

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-xs">
            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-[10px] font-medium text-slate-500 block">
                Total Targets
              </span>
              <span className="text-sm font-semibold text-slate-900">
                {prometheus.targetCount} Scrape Jobs
              </span>
            </div>

            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-[10px] font-medium text-slate-500 block">
                Healthy Targets
              </span>
              <span
                className={`text-sm font-semibold ${
                  prometheus.healthyTargets === prometheus.targetCount
                    ? "text-emerald-600"
                    : "text-amber-600"
                }`}
              >
                {prometheus.healthyTargets} / {prometheus.targetCount}
              </span>
            </div>
          </div>
        </div>

        {/* CloudWatch Card */}
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-md bg-blue-50 text-blue-600 border border-blue-100">
                <Cloud className="h-4 w-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-slate-900">AWS CloudWatch</h4>
                <p className="text-[10px] text-slate-500">
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

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-xs">
            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-[10px] font-medium text-slate-500 block">
                AWS Region
              </span>
              <span className="text-sm font-semibold text-slate-900">
                {cloudwatch.region}
              </span>
            </div>

            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-[10px] font-medium text-slate-500 block">
                Availability
              </span>
              <span
                className={`text-sm font-semibold ${
                  cloudwatch.available ? "text-emerald-600" : "text-slate-500"
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
