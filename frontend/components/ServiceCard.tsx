import React from "react";
import { Server, Activity, AlertCircle, Cpu, HardDrive } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { ServiceHealthData } from "../lib/types";

interface ServiceCardProps {
  service: ServiceHealthData;
  onClick?: () => void;
}

export default function ServiceCard({ service, onClick }: ServiceCardProps) {
  const isHealthy = service.status === "Healthy";
  const isDegraded = service.status === "Degraded";

  const borderColor = isHealthy
    ? "border-border hover:border-emerald-700/50"
    : isDegraded
    ? "border-amber-800/80 hover:border-amber-600 shadow-[0_0_12px_-2px_rgba(245,158,11,0.15)]"
    : "border-rose-800/80 hover:border-rose-600 shadow-[0_0_12px_-2px_rgba(239,68,68,0.2)]";

  return (
    <div
      onClick={onClick}
      className={`rounded-lg bg-surface p-4 border transition-all duration-200 ${borderColor} flex flex-col justify-between cursor-pointer`}
    >
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-md ${
                isHealthy
                  ? "bg-slate-800/80 text-emerald-400"
                  : isDegraded
                  ? "bg-amber-950/60 text-amber-400"
                  : "bg-rose-950/60 text-rose-400"
              }`}
            >
              <Server className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm tracking-tight">
                {service.name}
              </h3>
              <p className="text-[11px] font-mono text-slate-400">
                Port {service.port} • {service.version}
              </p>
            </div>
          </div>
          <StatusBadge status={service.status} size="sm" pulse={!isHealthy} />
        </div>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-2 gap-2.5 my-3 bg-surface-subtle p-2.5 rounded-md border border-border/60">
          <div>
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Availability
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                service.availability >= 99.5
                  ? "text-emerald-400"
                  : "text-amber-400"
              }`}
            >
              {service.availability.toFixed(2)}%
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              P95 Latency
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                service.p95Latency > 200
                  ? "text-rose-400"
                  : service.p95Latency > 100
                  ? "text-amber-400"
                  : "text-slate-200"
              }`}
            >
              {service.p95Latency} ms
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Request Rate
            </span>
            <span className="text-sm font-bold font-mono text-slate-200">
              {service.requestRate} req/s
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Error Rate
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                service.errorRate > 1.0
                  ? "text-rose-400 font-semibold"
                  : service.errorRate > 0.1
                  ? "text-amber-400"
                  : "text-emerald-400"
              }`}
            >
              {service.errorRate.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Resource Usage Gauges */}
        <div className="space-y-2 mt-3 pt-2 border-t border-border/50">
          {/* CPU Bar */}
          <div>
            <div className="flex justify-between text-[11px] font-mono mb-1">
              <span className="flex items-center gap-1 text-slate-400">
                <Cpu className="h-3 w-3" /> CPU
              </span>
              <span
                className={
                  service.cpu > 80
                    ? "text-rose-400 font-semibold"
                    : service.cpu > 65
                    ? "text-amber-400"
                    : "text-slate-300"
                }
              >
                {service.cpu}%
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  service.cpu > 80
                    ? "bg-rose-500"
                    : service.cpu > 65
                    ? "bg-amber-500"
                    : "bg-cyan-500"
                }`}
                style={{ width: `${Math.min(100, service.cpu)}%` }}
              />
            </div>
          </div>

          {/* Memory Bar */}
          <div>
            <div className="flex justify-between text-[11px] font-mono mb-1">
              <span className="flex items-center gap-1 text-slate-400">
                <HardDrive className="h-3 w-3" /> Memory
              </span>
              <span
                className={
                  service.memory > 80
                    ? "text-rose-400 font-semibold"
                    : service.memory > 65
                    ? "text-amber-400"
                    : "text-slate-300"
                }
              >
                {service.memory}%
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  service.memory > 80
                    ? "bg-rose-500"
                    : service.memory > 65
                    ? "bg-amber-500"
                    : "bg-indigo-500"
                }`}
                style={{ width: `${Math.min(100, service.memory)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Dependencies Footer */}
      {service.dependencies.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-border/40 text-[11px] font-mono text-slate-400">
          <span>Downstream: </span>
          <span className="text-slate-300">
            {service.dependencies.join(", ")}
          </span>
        </div>
      )}
    </div>
  );
}
