# Dashboard (Next.js)

Reactive operations dashboard for the AI-Based Cloud Observability System. It
surfaces backend health, the audited incident trail, and lets you run anomaly
analyses against the Python backend.

## Stack

- Next.js 16 (App Router) + React 19, plain JavaScript (no TypeScript config).
- All API calls go through the Next dev/start server via a rewrite:
  `/backend/*` → `http://localhost:8000/*`. The browser stays same-origin, so
  no CORS is required for the dashboard itself.

## Run

1. Start the backend on port 8000:

   ```bash
   cd .. && .venv/bin/uvicorn backend.main:app --port 8000
   ```

2. Install and run the dashboard:

   ```bash
   cd dashboard
   npm install
   npm run dev        # http://localhost:3000
   ```

To point the proxy at a different backend (e.g. a deployed instance or the
docker-compose stack):

```bash
BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

## Production build

```bash
npm run build
npm run start        # http://localhost:3000
```

## Pages / features

- **Backend status** — status, version, and environment from `/backend/health`.
- **Run an anomaly analysis** — paste reference + telemetry windows as JSON,
  pick a detector (z-score / IQR / Isolation Forest), and POST to
  `/backend/api/analyze`. Results show findings, severity, and the audit block
  hash the run was recorded under.
- **Audit trail** — the full chained blocks from `/backend/api/audit` with a
  live chain-integrity verdict.

## Notes

- `NEXT_PUBLIC_*` variables are not used; the backend base URL is read
  server-side by the rewrite config (`BACKEND_URL`, default
  `http://localhost:8000`).
- `package-lock.json` is committed for reproducible installs.