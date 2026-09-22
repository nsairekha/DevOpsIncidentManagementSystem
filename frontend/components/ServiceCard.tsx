import React from "react";
import { Server } from "lucide-react";
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
    ? "border-slate-200"
    : isDegraded
    ? "border-amber-300"
    : "border-rose-300";

  return (
    <div
      onClick={onClick}
      className={`rounded-xl bg-white p-5 border ${borderColor} shadow-sm hover:shadow transition flex flex-col justify-between cursor-pointer`}
    >
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-lg ${
                isHealthy
                  ? "bg-emerald-50 text-emerald-600"
                  : isDegraded
                  ? "bg-amber-50 text-amber-600"
                  : "bg-rose-50 text-rose-600"
              }`}
            >
              <Server className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
                {service.name}
              </h3>
              <p className="text-[11px] text-slate-500">
                Port <span className="font-mono">{service.port}</span> • {service.version}
              </p>
            </div>
          </div>
          <StatusBadge status={service.status} size="sm" pulse={!isHealthy} />
        </div>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-2 gap-2.5 my-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <div>
            <span className="text-[11px] font-medium text-slate-500 block">
              Availability
            </span>
            <span
              className={`text-sm font-semibold ${
                service.availability >= 99.5
                  ? "text-emerald-600"
                  : "text-amber-600"
              }`}
            >
              {service.availability.toFixed(2)}%
            </span>
          </div>

          <div>
            <span className="text-[11px] font-medium text-slate-500 block">
              P95 Latency
            </span>
            <span
              className={`text-sm font-semibold ${
                service.p95Latency > 200
                  ? "text-rose-600"
                  : service.p95Latency > 100
                  ? "text-amber-600"
                  : "text-slate-900"
              }`}
            >
              {service.p95Latency} ms
            </span>
          </div>

          <div>
            <span className="text-[11px] font-medium text-slate-500 block">
              Request Rate
            </span>
            <span className="text-sm font-semibold text-slate-900">
              {service.requestRate} req/s
            </span>
          </div>

          <div>
            <span className="text-[11px] font-medium text-slate-500 block">
              Error Rate
            </span>
            <span
              className={`text-sm font-semibold ${
                service.errorRate > 1.0
                  ? "text-rose-600"
                  : service.errorRate > 0.1
                  ? "text-amber-600"
                  : "text-emerald-600"
              }`}
            >
              {service.errorRate.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Resource Usage Gauges */}
        <div className="space-y-2 mt-3 pt-2 border-t border-slate-100">
          {/* CPU Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="flex items-center gap-1 text-slate-500">
                CPU
              </span>
              <span
                className={
                  service.cpu > 80
                    ? "text-rose-600 font-semibold"
                    : service.cpu > 65
                    ? "text-amber-600"
                    : "text-slate-900"
                }
              >
                {service.cpu}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  service.cpu > 80
                    ? "bg-rose-500"
                    : service.cpu > 65
                    ? "bg-amber-500"
                    : "bg-indigo-500"
                }`}
                style={{ width: `${Math.min(100, service.cpu)}%` }}
              />
            </div>
          </div>

          {/* Memory Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="flex items-center gap-1 text-slate-500">
                Memory
              </span>
              <span
                className={
                  service.memory > 80
                    ? "text-rose-600 font-semibold"
                    : service.memory > 65
                    ? "text-amber-600"
                    : "text-slate-900"
                }
              >
                {service.memory}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  service.memory > 80
                    ? "bg-rose-500"
                    : service.memory > 65
                    ? "bg-amber-500"
                    : "bg-blue-500"
                }`}
                style={{ width: `${Math.min(100, service.memory)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Dependencies Footer */}
      {service.dependencies.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-slate-500">
          <span>Downstream: </span>
          <span className="text-slate-900">
            {service.dependencies.join(", ")}
          </span>
        </div>
      )}
    </div>
  );
}
