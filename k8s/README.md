# Kubernetes manifests

Declarative deployment of the AI-Based Cloud Observability System onto
Kubernetes: the FastAPI backend and a Prometheus scraper, all in the
`observability` namespace.

## Layout

| Path | Kind | Purpose |
|---|---|---|
| `backend/namespace.yaml` | Namespace `observability` | Isolates the platform's workload |
| `backend/configmap.yaml` | ConfigMap | App configuration (`APP_ENV`, `APP_NAME`) |
| `backend/deployment.yaml` | Deployment | 2 replicas of the backend image, probes, resource bounds |
| `backend/service.yaml` | Service (ClusterIP) | `backend:80` -> container port 8000 |
| `prometheus/configmap.yaml` | ConfigMap | Scrape config: `backend:80/metrics` every 15s |
| `prometheus/deployment.yaml` | Deployment | Prometheus single replica mounting the config |
| `prometheus/service.yaml` | Service (ClusterIP) | `prometheus:9090` |

## Requirements

- A Kubernetes cluster and `kubectl` configured to talk to it
  (`kubectl cluster-info`). For local development, `minikube`, `kind`, or
  Docker Desktop's built-in Kubernetes all work.
- The backend image. Either build it locally:

  ```bash
  docker build -t ai-cloud-observability:latest .
  ```

  and, when using a cluster like `kind`/`minikube`, load it into the cluster:

  ```bash
  kind load docker-image ai-cloud-observability:latest        # kind
  minikube image load ai-cloud-observability:latest           # minikube
  ```

  or push it to a registry and change `image:` in `deployment.yaml`
  accordingly (the manifests use `imagePullPolicy: IfNotPresent`).

## Apply

```bash
kubectl apply -f k8s/backend/
kubectl apply -f k8s/prometheus/
```

Check rollout status:

```bash
kubectl -n observability rollout status deployment/backend
kubectl -n observability get pods,svc,cm -n observability
```

## Verify

Port-forward the backend service and hit its endpoints:

```bash
kubectl -n observability port-forward svc/backend 8000:80
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

Port-forward Prometheus and confirm it is scraping the backend:

```bash
kubectl -n observability port-forward svc/prometheus 9090:9090
# open http://127.0.0.1:9090 -> Status > Targets: backend should be UP
# or query: http_requests_total
```

## Notes

- The `backend` Service exposes port 80 pointing at the container's `http`
  (8000) port; Prometheus scrapes `backend:80/metrics` cluster-internally.
- Deployment manifests include readiness/liveness probes against `/health`
  and resource requests/limits so the scheduler can place and protect them.
- Tear everything down with `kubectl delete -f k8s/` (both directories).