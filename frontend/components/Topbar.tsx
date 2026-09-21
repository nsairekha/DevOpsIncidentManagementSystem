"use client";

import React, { useState } from "react";
import {
  Menu,
  Search,
  Bell,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Server,
  ExternalLink,
  ChevronDown,
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
    <header className="sticky top-0 z-30 h-16 bg-[#090d16]/90 backdrop-blur-md border-b border-border/80 px-4 lg:px-6 flex items-center justify-between gap-4">
      {/* Left: Mobile Toggle & Project Name */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <h1 className="text-sm sm:text-base font-bold text-white tracking-tight flex items-center gap-2">
            <span>AI Cloud Observability</span>
            <span className="hidden sm:inline-block text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 font-medium">
              SRE PLATFORM
            </span>
          </h1>
        </div>
      </div>

      {/* Center: Search Bar */}
      <div className="hidden md:flex flex-1 max-w-md mx-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search traces, services, metrics or incidents (Press '/' to focus)"
            className="w-full pl-9 pr-4 py-1.5 bg-surface-subtle border border-border rounded-lg text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-all"
          />
        </div>
      </div>

      {/* Right: Environment Selector, Status, Notifications, Refresh */}
      <div className="flex items-center gap-3">
        {/* Environment Selector */}
        <div className="flex items-center bg-surface-subtle p-1 rounded-lg border border-border">
          <button
            onClick={() => onEnvironmentChange("Local")}
            className={`px-2.5 py-1 text-xs font-mono rounded-md transition-all ${
              environment === "Local"
                ? "bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Local
          </button>
          <button
            onClick={() => onEnvironmentChange("AWS")}
            className={`px-2.5 py-1 text-xs font-mono rounded-md transition-all ${
              environment === "AWS"
                ? "bg-indigo-950 text-indigo-300 font-semibold border border-indigo-800/60 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            AWS
          </button>
        </div>

        {/* Current System Status Badge */}
        <div className="hidden sm:flex items-center">
          <StatusBadge
            status={systemStatus}
            size="md"
            pulse={systemStatus !== "Operational"}
          />
        </div>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh live telemetry"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface border border-transparent hover:border-border transition-all"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? "animate-spin text-cyan-400" : ""}`}
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
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface border border-transparent hover:border-border transition-all relative"
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
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-lg bg-surface border border-border shadow-2xl p-4 z-50 animate-in fade-in-50 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <h4 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  Operational Alerts
                </h4>
                <span className="text-[10px] font-mono text-cyan-400">
                  3 active notifications
                </span>
              </div>

              <div className="divide-y divide-border/60 max-h-72 overflow-y-auto my-2">
                {notifications.map((n) => (
                  <div key={n.id} className="py-2.5 space-y-1 hover:bg-surface-subtle/50 px-1 rounded transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-200">
                        {n.title}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        {n.time}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">
                      {n.message}
                    </p>
                    <div className="pt-0.5">
                      <StatusBadge status={n.severity} size="sm" />
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-border flex justify-between items-center text-[11px] font-mono">
                <span className="text-slate-400">Automated AI alerts</span>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-cyan-400 hover:underline"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
