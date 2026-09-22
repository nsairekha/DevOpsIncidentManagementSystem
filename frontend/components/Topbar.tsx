"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import {
  Menu,
  Search,
  Bell,
  RefreshCw,
} from "lucide-react";
import StatusBadge from "./StatusBadge";
import { Environment, SystemStatus } from "../lib/types";

interface TopbarProps {
  systemStatus?: SystemStatus;
  environment: Environment;
  onEnvironmentChange: (env: Environment) => void;
  onToggleSidebar: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export default function Topbar({
  systemStatus = "Operational",
  environment,
  onEnvironmentChange,
  onToggleSidebar,
  onRefresh,
  isRefreshing = false,
}: TopbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(2);
  const pathname = usePathname();

  const pageTitles: Record<string, string> = {
    "/dashboard": "Overview",
    "/services": "Services",
    "/metrics": "Metrics",
    "/anomalies": "Anomalies",
    "/rca": "Root Cause Analysis",
    "/incidents": "Incidents",
    "/blockchain": "Blockchain Audit",
  };
  const currentPage =
    pageTitles[pathname] ||
    pathname.split("/").filter(Boolean).pop()?.replace("-", " ") ||
    "Overview";

  const notifications = [
    {
      id: 1,
      title: "Payment Service Latency Spike",
      time: "8m ago",
      severity: "Critical",
      message: "p95 latency breached 450ms SLA (current: 850ms).",
    },
    {
      id: 2,
      title: "Cascading Incident INC-4088",
      time: "24m ago",
      severity: "High",
      message: "Order Service failure rate increased due to downstream timeouts.",
    },
    {
      id: 3,
      title: "Ledger Consensus Block #5 Audited",
      time: "32m ago",
      severity: "Low",
      message: "Cryptographic hash verified by ConsensusAgent.",
    },
  ];

  return (
    <header className="sticky top-0 z-30 h-14 bg-white/80 backdrop-blur border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between gap-4">
      {/* Left: Mobile Toggle + breadcrumb title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 -ml-2 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[13px] text-slate-400 hidden sm:inline">
            Home
          </span>
          <span className="text-[13px] text-slate-300 hidden sm:inline">/</span>
          <h1 className="text-[13px] font-semibold text-slate-900 capitalize truncate">
            {currentPage}
          </h1>
        </div>
      </div>

      {/* Center: Search Bar */}
      <div className="hidden md:flex flex-1 max-w-sm mx-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search services, incidents…"
            className="w-full pl-9 pr-10 py-1.5 bg-slate-100/70 border border-transparent rounded-full text-[13px] text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-slate-300 transition-all"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-medium text-slate-400 bg-white border border-slate-200 rounded px-1.5 py-0.5">
            /
          </kbd>
        </div>
      </div>

      {/* Right: Environment Selector, Status, Notifications, Refresh */}
      <div className="flex items-center gap-1.5">
        {/* Environment Selector */}
        <div className="flex items-center bg-slate-100 rounded-full p-0.5 border border-slate-200/70">
          {(["Local", "AWS"] as Environment[]).map((env) => (
            <button
              key={env}
              onClick={() => onEnvironmentChange(env)}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-full transition-all ${
                environment === env
                  ? "bg-white text-slate-900 font-medium shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  env === "Local" ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {env}
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-slate-200 mx-1 hidden sm:block" />

        {/* Current System Status Badge */}
        <div className="hidden sm:flex items-center">
          <StatusBadge
            status={systemStatus}
            size="sm"
            pulse={systemStatus !== "Operational"}
          />
        </div>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh live telemetry"
            className="p-2 rounded-full text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-all"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? "animate-spin text-slate-900" : ""}`}
            />
          </button>
        )}

        {/* Notification Bell with Popover */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setUnreadCount(0);
            }}
            className="p-2 rounded-full text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-all relative"
            aria-label="View system notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-white border border-slate-200 shadow-xl shadow-slate-200/50 p-2 z-50">
              <div className="flex items-center justify-between px-3 py-2">
                <h4 className="text-[13px] font-semibold text-slate-900">
                  Notifications
                </h4>
                <span className="text-[11px] text-slate-400">
                  3 new
                </span>
              </div>

              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="py-2.5 px-3 space-y-1 hover:bg-slate-50 rounded-lg transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-900">
                        {n.title}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {n.time}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug">
                      {n.message}
                    </p>
                    <div className="pt-0.5">
                      <StatusBadge status={n.severity} size="sm" />
                    </div>
                  </div>
                ))}
              </div>

              <div className="px-3 py-2 border-t border-slate-100 flex justify-between items-center">
                <span className="text-[11px] text-slate-400">Auto-refresh every 15s</span>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-[12px] font-medium text-slate-900 hover:underline"
                >
                  View all
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
