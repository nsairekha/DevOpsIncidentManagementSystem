"use client";

import React, { useState } from "react";
import { Globe, Server, AlertTriangle } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { ServiceHealthData } from "../lib/types";

interface ServiceMapProps {
  services?: ServiceHealthData[];
}

export default function ServiceMap({ services }: ServiceMapProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Map service lookup
  const getService = (id: string) => {
    return services?.find((s) => s.id === id);
  };

  const orderService = getService("order-service");
  const paymentService = getService("payment-service");
  const notificationService = getService("notification-service");
  const userService = getService("user-service");

  const isPaymentDegraded =
    paymentService?.status === "Degraded" || paymentService?.status === "Down";
  const isOrderDegraded =
    orderService?.status === "Degraded" || orderService?.status === "Down";

  return (
    <div className="rounded-xl bg-white border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
            Distributed Service Topology
          </h3>
          <p className="text-[11px] text-slate-500">
            Live dependency graph &amp; failure propagation
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Healthy Edge
          </span>
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full bg-amber-500" />{" "}
            Degraded Edge
          </span>
        </div>
      </div>

      {/* Visual Service Topology Container */}
      <div className="relative bg-slate-50 border border-slate-200 rounded-xl p-6 overflow-x-auto min-w-[620px]">
        {/* SVG connection lines overlay */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ minWidth: "620px" }}
        >
          <defs>
            <marker
              id="arrow-green"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#059669" />
            </marker>
            <marker
              id="arrow-amber"
              viewBox="0 0 10 10"
              refX="6"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#D97706" />
            </marker>
          </defs>

          {/* Client to User Service line */}
          <path
            d="M 120 185 C 120 70, 240 70, 260 70"
            fill="none"
            stroke="#059669"
            strokeWidth="2"
            strokeDasharray="4 2"
            markerEnd="url(#arrow-green)"
          />

          {/* Client to Order Service line */}
          <path
            d="M 160 215 L 260 215"
            fill="none"
            stroke="#059669"
            strokeWidth="2"
            markerEnd="url(#arrow-green)"
          />

          {/* Order Service to Payment Service (Degraded connection) */}
          <path
            d="M 450 195 C 490 195, 490 130, 520 130"
            fill="none"
            stroke={isPaymentDegraded ? "#D97706" : "#059669"}
            strokeWidth={isPaymentDegraded ? "2.5" : "2"}
            strokeDasharray={isPaymentDegraded ? "6 3" : "none"}
            markerEnd={isPaymentDegraded ? "url(#arrow-amber)" : "url(#arrow-green)"}
          />

          {/* Order Service to Notification Service */}
          <path
            d="M 450 235 C 490 235, 490 290, 520 290"
            fill="none"
            stroke="#059669"
            strokeWidth="2"
            markerEnd="url(#arrow-green)"
          />
        </svg>

        {/* Nodes Grid */}
        <div className="relative z-10 grid grid-cols-3 gap-8 items-center min-h-[340px]">
          {/* Column 1: Client Ingress */}
          <div className="flex flex-col items-center justify-center">
            <div
              onClick={() => setSelectedNode("client")}
              className="w-40 rounded-xl bg-white border border-slate-200 p-3 shadow-sm hover:border-indigo-300 cursor-pointer transition-all text-center"
            >
              <div className="mx-auto w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-2">
                <Globe className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-semibold text-slate-900">Client Traffic</h4>
              <p className="text-[10px] text-slate-500">External Gateway</p>
              <div className="mt-2 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                1,420 req/s
              </div>
            </div>
          </div>

          {/* Column 2: Core Middleware Services */}
          <div className="flex flex-col gap-10">
            {/* User Service Node */}
            <div
              onClick={() => setSelectedNode("user-service")}
              className={`rounded-xl bg-white border p-3.5 shadow-sm cursor-pointer transition-all ${
                selectedNode === "user-service"
                  ? "border-indigo-500 ring-1 ring-indigo-500"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Server className="h-3.5 w-3.5 text-slate-400" />
                  User Service
                </span>
                <StatusBadge
                  status={userService?.status || "Healthy"}
                  size="sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] mt-2 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
                <span className="text-slate-500">
                  Lat:{" "}
                  <strong className="text-slate-900">
                    {userService?.p95Latency || 18}ms
                  </strong>
                </span>
                <span className="text-slate-500">
                  Err:{" "}
                  <strong className="text-emerald-600">
                    {userService?.errorRate || 0.02}%
                  </strong>
                </span>
              </div>
            </div>

            {/* Order Service Node */}
            <div
              onClick={() => setSelectedNode("order-service")}
              className={`rounded-xl bg-white border p-3.5 shadow-sm cursor-pointer transition-all ${
                isOrderDegraded
                  ? "border-amber-300 bg-amber-50/30"
                  : "border-slate-200 hover:border-slate-300"
              } ${
                selectedNode === "order-service"
                  ? "ring-1 ring-indigo-500 border-indigo-500"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Server className="h-3.5 w-3.5 text-slate-400" />
                  Order Service
                </span>
                <StatusBadge
                  status={orderService?.status || "Degraded"}
                  size="sm"
                  pulse={isOrderDegraded}
                />
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] mt-2 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
                <span className="text-slate-500">
                  Lat:{" "}
                  <strong className="text-amber-600">
                    {orderService?.p95Latency || 142}ms
                  </strong>
                </span>
                <span className="text-slate-500">
                  Err:{" "}
                  <strong className="text-rose-600">
                    {orderService?.errorRate || 1.45}%
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* Column 3: Downstream Dependencies */}
          <div className="flex flex-col gap-10">
            {/* Payment Service Node */}
            <div
              onClick={() => setSelectedNode("payment-service")}
              className={`rounded-xl bg-white border p-3.5 shadow-sm cursor-pointer transition-all ${
                isPaymentDegraded
                  ? "border-amber-300 bg-amber-50/30"
                  : "border-slate-200 hover:border-slate-300"
              } ${
                selectedNode === "payment-service"
                  ? "ring-1 ring-indigo-500 border-indigo-500"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Server className="h-3.5 w-3.5 text-slate-400" />
                  Payment Service
                </span>
                <StatusBadge
                  status={paymentService?.status || "Degraded"}
                  size="sm"
                  pulse={isPaymentDegraded}
                />
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] mt-2 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
                <span className="text-slate-500">
                  Lat:{" "}
                  <strong className="text-rose-600 font-semibold">
                    {paymentService?.p95Latency || 480}ms
                  </strong>
                </span>
                <span className="text-slate-500">
                  Err:{" "}
                  <strong className="text-rose-600">
                    {paymentService?.errorRate || 2.8}%
                  </strong>
                </span>
              </div>
              {isPaymentDegraded && (
                <div className="mt-2 text-[10px] font-medium text-amber-700 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-amber-600 shrink-0" />
                  Root cause: Latency bottle-neck
                </div>
              )}
            </div>

            {/* Notification Service Node */}
            <div
              onClick={() => setSelectedNode("notification-service")}
              className={`rounded-xl bg-white border p-3.5 shadow-sm cursor-pointer transition-all ${
                selectedNode === "notification-service"
                  ? "border-indigo-500 ring-1 ring-indigo-500"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Server className="h-3.5 w-3.5 text-slate-400" />
                  Notification Service
                </span>
                <StatusBadge
                  status={notificationService?.status || "Healthy"}
                  size="sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] mt-2 bg-slate-50 p-1.5 rounded-lg border border-slate-200">
                <span className="text-slate-500">
                  Lat:{" "}
                  <strong className="text-slate-900">
                    {notificationService?.p95Latency || 12}ms
                  </strong>
                </span>
                <span className="text-slate-500">
                  Err:{" "}
                  <strong className="text-emerald-600">
                    {notificationService?.errorRate || 0.0}%
                  </strong>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span className="text-[11px]">
          Topology updates in real time based on active service probes
        </span>
        <span className="text-[11px] text-indigo-600">
          Sync: Every 15s
        </span>
      </div>
    </div>
  );
}
