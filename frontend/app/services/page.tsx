"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Server, RefreshCw, Layers, ShieldCheck, Activity, Info } from "lucide-react";
import ServiceCard from "../../components/ServiceCard";
import ServiceMap from "../../components/ServiceMap";
import StatusBadge from "../../components/StatusBadge";
import RefreshIndicator from "../../components/RefreshIndicator";
import { LoadingState, ErrorState } from "../../components/LoadingState";
import { API_BASE_URL, fetchServicesData } from "../../lib/api";
import { DEMO_SERVICES } from "../../lib/demo-data";
import { ServiceHealthData } from "../../lib/types";

export default function ServicesPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [allowFallback, setAllowFallback] = useState(true);

  const [services, setServices] = useState<ServiceHealthData[]>([]);
  const [selectedService, setSelectedService] = useState<ServiceHealthData | null>(
    null
  );

  const loadServices = useCallback(async () => {
    try {
      setRefreshing(true);
      setError(null);

      const res = await fetchServicesData();

      if (res.isLive) {
        setIsLive(true);
        setServices(res.services);
        if (!selectedService && res.services.length > 0) {
          setSelectedService(res.services[0]);
        }
      } else {
        setIsLive(false);
        setError(res.error || "Backend API is offline at " + API_BASE_URL);

        if (allowFallback) {
          setServices(DEMO_SERVICES);
          if (!selectedService) setSelectedService(DEMO_SERVICES[0]);
        } else {
          setServices([]);
        }
      }

      setLastUpdated(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load services";
      setError(msg);
      setIsLive(false);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [allowFallback, selectedService]);

  useEffect(() => {
    loadServices();
  }, [loadServices]);

  if (loading && services.length === 0) {
    return <LoadingState type="cards" message="Connecting to service fleet registry..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg bg-surface border border-border">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            {isLive && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isLive ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
          </span>
          <div className="text-xs font-mono">
            <span className="font-bold text-white uppercase tracking-wide">
              {isLive ? "LIVE SERVICE TELEMETRY" : "DEMO DATA (Backend Offline)"}
            </span>
            <span className="text-slate-400 ml-2">
              Source: {isLive ? "FastAPI /api/v1/metrics/summary" : "Isolated Demo Store"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RefreshIndicator
            lastUpdated={lastUpdated}
            onRefresh={loadServices}
            intervalSeconds={10}
            isRefreshing={refreshing}
          />

          {!isLive && (
            <button
              onClick={() => setAllowFallback(!allowFallback)}
              className="text-[11px] font-mono px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              {allowFallback ? "Hide Demo Data" : "Show Demo Data"}
            </button>
          )}
        </div>
      </div>

      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">
          Microservice Fleet Health
        </h2>
        <p className="text-xs font-mono text-slate-400">
          User Service, Order Service, Payment Service, and Notification Service diagnostics
        </p>
      </div>

      {/* Service Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((service) => (
          <ServiceCard
            key={service.id}
            service={service}
            onClick={() => setSelectedService(service)}
          />
        ))}
      </div>

      {/* Distributed Service Map */}
      <ServiceMap services={services} />

      {/* Selected Service Detailed Inspector */}
      {selectedService && (
        <div className="rounded-lg bg-surface border border-border p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-border/80 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-slate-800 text-cyan-400 border border-slate-700">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">
                  {selectedService.name} Specification & Diagnostics
                </h3>
                <p className="text-xs font-mono text-slate-400">
                  Service ID: <code>{selectedService.id}</code> • Host Port:{" "}
                  <code>{selectedService.port}</code>
                </p>
              </div>
            </div>
            <StatusBadge
              status={selectedService.status}
              size="md"
              pulse={selectedService.status !== "Healthy"}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-lg bg-surface-subtle border border-border/70 space-y-2">
              <span className="text-slate-400 uppercase text-[10px] block">
                Network & Endpoints
              </span>
              <div className="space-y-1 text-slate-300">
                <div>Health Check: <code className="text-cyan-400">GET /health</code></div>
                <div>API Info: <code className="text-cyan-400">GET /api/v1/</code></div>
                <div>Metrics: <code className="text-cyan-400">GET /metrics</code></div>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-surface-subtle border border-border/70 space-y-2">
              <span className="text-slate-400 uppercase text-[10px] block">
                Downstream Dependencies
              </span>
              {selectedService.dependencies.length > 0 ? (
                <div className="space-y-1">
                  {selectedService.dependencies.map((dep) => (
                    <div key={dep} className="flex items-center justify-between">
                      <span className="text-slate-300">→ {dep}</span>
                      <span className="text-[10px] text-amber-400">HTTP REST</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-slate-500">None (Edge / Leaf service)</div>
              )}
            </div>

            <div className="p-3.5 rounded-lg bg-surface-subtle border border-border/70 space-y-2">
              <span className="text-slate-400 uppercase text-[10px] block">
                SRE Health Assessment
              </span>
              <div className="space-y-1">
                <div>Availability: <span className="font-bold text-white">{selectedService.availability}%</span></div>
                <div>Latency p95: <span className="font-bold text-white">{selectedService.p95Latency}ms</span></div>
                <div>CPU Load: <span className="font-bold text-white">{selectedService.cpu}%</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
