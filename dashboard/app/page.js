"use client";

import { useCallback, useEffect, useState } from "react";

const DEFAULT_REFERENCE = JSON.stringify(
  { cpu: [10.0, 10.5, 9.8, 10.2, 10.1, 9.9, 10.3, 10.0] },
  null,
  2
);
const DEFAULT_TELEMETRY = JSON.stringify(
  { cpu: [10.2, 9.9, 10.0, 10.1, 98.0, 10.3] },
  null,
  2
);

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} -> HTTP ${response.status}`);
  return response.json();
}

export default function Page() {
  const [health, setHealth] = useState(null);
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState(null);

  const [reference, setReference] = useState(DEFAULT_REFERENCE);
  const [telemetry, setTelemetry] = useState(DEFAULT_TELEMETRY);
  const [detector, setDetector] = useState("zscore");
  const [analysis, setAnalysis] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [h, a] = await Promise.all([
        fetchJson("/backend/health"),
        fetchJson("/backend/api/audit"),
      ]);
      setHealth(h);
      setAudit(a);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function runAnalysis(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = {
        reference: JSON.parse(reference),
        telemetry: JSON.parse(telemetry),
        detector,
      };
      const response = await fetch("/backend/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`analyze -> HTTP ${response.status}`);
      setAnalysis(await response.json());
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container">
      <h1>AI Cloud Observability</h1>

      {error && <p className="error">⚠ {error} — is the backend running?</p>}

      <section className="card">
        <h2>Backend status</h2>
        {health ? (
          <dl className="grid">
            <div><dt>Status</dt><dd className={health.status === "ok" ? "ok" : ""}>{health.status}</dd></div>
            <div><dt>App</dt><dd>{health.app_name}</dd></div>
            <div><dt>Version</dt><dd>{health.version}</dd></div>
            <div><dt>Environment</dt><dd>{health.environment}</dd></div>
          </dl>
        ) : (
          <p>Loading…</p>
        )}
      </section>

      <section className="card">
        <h2>Run an anomaly analysis</h2>
        <form onSubmit={runAnalysis} className="form">
          <label>
            Detector
            <select value={detector} onChange={(e) => setDetector(e.target.value)}>
              <option value="zscore">z-score</option>
              <option value="iqr">IQR</option>
              <option value="isolation_forest">Isolation Forest</option>
            </select>
          </label>
          <label>
            Reference window (JSON)
            <textarea
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              rows={7}
              spellCheck={false}
            />
          </label>
          <label>
            Telemetry window (JSON)
            <textarea
              value={telemetry}
              onChange={(e) => setTelemetry(e.target.value)}
              rows={5}
              spellCheck={false}
            />
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Analysing…" : "Analyse"}
          </button>
        </form>

        {analysis && (
          <div className="result">
            <p>
              <strong>{analysis.n_findings}</strong> finding(s) · severity{" "}
              <strong>{analysis.severity}</strong>
            </p>
            <p className="muted">{analysis.summary}</p>
            {analysis.findings.length > 0 ? (
              <table>
                <thead>
                  <tr><th>Signal</th><th>Value</th><th>Score</th><th>Severity</th><th>Details</th></tr>
                </thead>
                <tbody>
                  {analysis.findings.map((f, i) => (
                    <tr key={i}>
                      <td>{f.signal}</td>
                      <td>{f.value.toFixed(3)}</td>
                      <td>{f.score.toFixed(2)}</td>
                      <td>{f.severity}</td>
                      <td className="muted">{f.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No anomalies detected.</p>
            )}
            {analysis.audited && (
              <p className="muted">
                Audited on-chain · block <code>{analysis.block_hash.slice(0, 12)}…</code> · event{" "}
                <code>{analysis.event_id.slice(0, 8)}…</code>
              </p>
            )}
          </div>
        )}
      </section>

      <section className="card">
        <h2>Audit trail {audit && <span className="badge">{audit.length} blocks</span>}</h2>
        {audit ? (
          <>
            <p className={audit.valid ? "ok" : "error"}>
              Chain integrity: {audit.valid ? "valid" : "VIOLATED"}
            </p>
            <table>
              <thead>
                <tr><th>Index</th><th>Event</th><th>Timestamp</th><th>Hash</th><th>Previous</th></tr>
              </thead>
              <tbody>
                {audit.blocks.map((b) => (
                  <tr key={b.index}>
                    <td>{b.index}</td>
                    <td>{b.event_type}</td>
                    <td className="muted">{b.timestamp}</td>
                    <td><code>{b.hash.slice(0, 10)}…</code></td>
                    <td><code>{b.previous_hash.slice(0, 10)}…</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p>Loading…</p>
        )}
      </section>
    </main>
  );
}