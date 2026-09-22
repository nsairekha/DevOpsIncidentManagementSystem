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

  const navSections = [
    {
      label: "Observe",
      items: [
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
      ],
    },
    {
      label: "Respond",
      items: [
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
      ],
    },
  ];

  const renderNavItem = (item: {
    name: string;
    href: string;
    icon: React.ElementType;
  }) => {
    const Icon = item.icon;
    const isActive =
      pathname === item.href ||
      (item.href !== "/dashboard" && pathname.startsWith(item.href));

    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onClose}
        className={`group flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all ${
          isActive
            ? "bg-slate-900 text-white font-medium shadow-sm"
            : "text-slate-500 hover:text-slate-900 hover:bg-slate-100 font-normal"
        }`}
      >
        <Icon
          className={`h-[17px] w-[17px] shrink-0 ${
            isActive ? "text-white" : "text-slate-400 group-hover:text-slate-600"
          }`}
        />
        <span className="truncate">{item.name}</span>
        {item.name === "Incidents" && (
          <span className="ml-auto px-1.5 py-px rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            1
          </span>
        )}
        {item.name === "Anomalies" && (
          <span className="ml-auto px-1.5 py-px rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            5
          </span>
        )}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/40 lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-60 bg-white border-r border-slate-200 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Top Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-slate-100">
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5 tracking-tight"
          >
            <div className="w-8 h-8 rounded-[10px] bg-slate-900 flex items-center justify-center text-white shadow-sm">
              <Radio className="h-4 w-4" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-[13px] font-semibold text-slate-900">
                Observability
              </span>
              <span className="text-[11px] text-slate-400 font-normal mt-0.5">
                SRE Dashboard
              </span>
            </div>
          </Link>

          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-5 overflow-y-auto">
          {navSections.map((section) => (
            <div key={section.label}>
              <div className="px-3 pb-1.5 text-[11px] font-medium tracking-wide text-slate-400">
                {section.label}
              </div>
              <div className="space-y-0.5">
                {section.items.map(renderNavItem)}
              </div>
            </div>
          ))}
        </nav>

        {/* BOTTOM SIDEBAR */}
        <div className="p-3 border-t border-slate-100 space-y-2">
          {/* System Status Display */}
          <div className="px-3 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center gap-2.5">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <div className="flex flex-col min-w-0">
              <span className="text-[11px] text-slate-400 leading-none">
                System Status
              </span>
              <span className="text-[13px] font-medium text-slate-900 leading-tight mt-0.5">
                {systemStatus}
              </span>
            </div>
            <div className="ml-auto">
              <StatusBadge
                status={systemStatus}
                size="sm"
                pulse={systemStatus !== "Operational"}
              />
            </div>
          </div>

          {/* Settings + user row */}
          <div className="flex items-center gap-1">
            <button
              onClick={onOpenSettings}
              className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-slate-900 text-white text-[11px] font-semibold flex items-center justify-center shrink-0">
              SR
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
