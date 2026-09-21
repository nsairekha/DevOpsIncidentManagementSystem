"use client";

import React, { useState } from "react";
import { X, Save, Sliders, ShieldCheck } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [refreshInterval, setRefreshInterval] = useState("15");
  const [backendUrl, setBackendUrl] = useState("http://localhost:8000");
  const [prometheusUrl, setPrometheusUrl] = useState("http://localhost:9090");
  const [anomalySensitivity, setAnomalySensitivity] = useState("3.0");
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-xl bg-surface border border-border shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-slate-900/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-slate-800 text-cyan-400">
              <Sliders className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Observability Settings
              </h3>
              <p className="text-[11px] font-mono text-slate-400">
                Configure polling, ingestion & AI thresholds
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-4 text-xs font-mono">
          <div>
            <label className="block text-slate-300 mb-1 font-semibold">
              Telemetry Refresh Interval
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="5">Every 5 seconds (Real-time)</option>
              <option value="15">Every 15 seconds (Recommended)</option>
              <option value="30">Every 30 seconds</option>
              <option value="60">Every 60 seconds</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1 font-semibold">
              FastAPI Backend Endpoint
            </label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 mb-1 font-semibold">
              Prometheus Endpoint
            </label>
            <input
              type="text"
              value={prometheusUrl}
              onChange={(e) => setPrometheusUrl(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 mb-1 font-semibold">
              Z-Score Anomaly Threshold (Standard Deviations)
            </label>
            <input
              type="number"
              step="0.1"
              min="1.0"
              max="6.0"
              value={anomalySensitivity}
              onChange={(e) => setAnomalySensitivity(e.target.value)}
              className="w-full bg-surface-subtle border border-border rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">
              Default is 3.0σ. Lower values increase sensitivity to anomalies.
            </span>
          </div>

          <div className="pt-4 border-t border-border flex items-center justify-between">
            <span className="text-[10px] text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5" /> Client config active
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg border border-border text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-colors flex items-center gap-1.5"
              >
                <Save className="h-3.5 w-3.5" />
                {saved ? "Saved!" : "Save Settings"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
