"use client";

import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import SettingsModal from "./SettingsModal";
import { Environment, SystemStatus } from "../lib/types";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [environment, setEnvironment] = useState<Environment>("Local");
  const [systemStatus, setSystemStatus] = useState<SystemStatus>("Operational");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Trigger window event so any active page listener can refetch
    window.dispatchEvent(new CustomEvent("telemetry-refresh"));
    setTimeout(() => setIsRefreshing(false), 800);
  };

  return (
    <div className="min-h-screen bg-background text-slate-100 flex">
      {/* Left Sidebar */}
      <Sidebar
        systemStatus={systemStatus}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64 transition-all duration-300">
        {/* Topbar */}
        <Topbar
          systemStatus={systemStatus}
          environment={environment}
          onEnvironmentChange={setEnvironment}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}
