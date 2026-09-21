"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Server,
  Activity,
  AlertTriangle,
  GitPullRequest,
  ShieldAlert,
  Blocks,
  Settings,
  X,
  Radio,
} from "lucide-react";
import StatusBadge from "./StatusBadge";
import { SystemStatus } from "../lib/types";

interface SidebarProps {
  systemStatus?: SystemStatus;
  isOpen?: boolean;
  onClose?: () => void;
  onOpenSettings?: () => void;
}

export default function Sidebar({
  systemStatus = "Operational",
  isOpen = false,
  onClose,
  onOpenSettings,
}: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Overview",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Services",
      href: "/services",
      icon: Server,
    },
    {
      name: "Metrics",
      href: "/metrics",
      icon: Activity,
    },
    {
      name: "Anomalies",
      href: "/anomalies",
      icon: AlertTriangle,
    },
    {
      name: "Root Cause Analysis",
      href: "/rca",
      icon: GitPullRequest,
    },
    {
      name: "Incidents",
      href: "/incidents",
      icon: ShieldAlert,
    },
    {
      name: "Blockchain Audit",
      href: "/blockchain",
      icon: Blocks,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-64 bg-[#090d16] border-r border-border/80 flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Top Header */}
        <div>
          <div className="h-16 flex items-center justify-between px-5 border-b border-border/60">
            <Link
              href="/dashboard"
              className="flex items-center gap-2.5 font-bold text-white tracking-tight"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-900/30">
                <Radio className="h-4 w-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold leading-tight">
                  AI Observability
                </span>
                <span className="text-[10px] font-mono text-cyan-400 font-normal">
                  Distributed SRE v1.0
                </span>
              </div>
            </Link>

            {onClose && (
              <button
                onClick={onClose}
                className="lg:hidden p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-210px)]">
            <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Telemetry & Ops
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? "bg-slate-800/90 text-cyan-400 border border-slate-700 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 ${
                      isActive ? "text-cyan-400" : "text-slate-400"
                    }`}
                  />
                  <span>{item.name}</span>
                  {item.name === "Incidents" && (
                    <span className="ml-auto px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-400 border border-rose-800/60">
                      1
                    </span>
                  )}
                  {item.name === "Anomalies" && (
                    <span className="ml-auto px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-400 border border-amber-800/60">
                      5
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* BOTTOM SIDEBAR */}
        <div className="p-3 border-t border-border/80 bg-[#070a11] space-y-2">
          {/* System Status Display */}
          <div className="p-2.5 rounded-md bg-surface border border-border/60 flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] font-mono uppercase text-slate-400">
                System Status
              </span>
              <span className="text-xs font-semibold text-slate-200">
                {systemStatus}
              </span>
            </div>
            <StatusBadge
              status={systemStatus}
              size="sm"
              pulse={systemStatus !== "Operational"}
            />
          </div>

          {/* Settings Trigger */}
          <button
            onClick={onOpenSettings}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          >
            <Settings className="h-4 w-4 text-slate-500" />
            <span>Settings</span>
            <span className="ml-auto text-[10px] font-mono text-slate-400">
              config
            </span>
          </button>
        </div>
      </aside>
    </>
  );
}
