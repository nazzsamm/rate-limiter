# Rate Limiter Service

A lightweight HTTP rate limiter service that limits requests by IP address, built with Python (FastAPI), Redis, and deployed on Kubernetes.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Deployment](#deployment)
  - [Local Testing with Docker Compose](#local-testing-with-docker-compose)
  - [Kubernetes Deployment](#kubernetes-deployment)
- [Interacting with the Service](#interacting-with-the-service)
- [API Reference](#api-reference)

---

## Overview

The rate limiter service controls the number of HTTP requests a user can make based on their IP address. If a user exceeds the allowed number of requests per second, the service returns HTTP `429 Too Many Requests`. Otherwise, it returns HTTP `200 OK`.

Key features:
- Rate limits requests per IP address
- Configurable endpoint and request limit via environment variables
- Persistent state stored in Redis — survives service crashes and restarts
- Health check endpoint for Kubernetes liveness probes
- Fully containerised and deployable to a Kubernetes cluster

---

## Architecture

```
┌─────────────────────────────────────────┐
│            Kubernetes Cluster           │
│                                         │
│  ┌──────────────────┐                   │
│  │  Rate Limiter    │  ←── HTTP Request │
│  │  (FastAPI/Python)│                   │
│  └────────┬─────────┘                   │
│           │                             │
│  ┌────────▼─────────┐                   │
│  │      Redis       │                   │
│  │  (State Storage) │                   │
│  └──────────────────┘                   │
└─────────────────────────────────────────┘
```

- **Rate Limiter** — Python FastAPI app that intercepts requests and checks rate limit state
- **Redis** — stores request counts per IP per second; state persists across service restarts

---

## Prerequisites

Make sure the following tools are installed before deploying:

| Tool | Purpose | Download |
|------|---------|----------|
| Docker Desktop | Build and run containers | https://www.docker.com/products/docker-desktop |
| Minikube | Local Kubernetes cluster | https://minikube.sigs.k8s.io/docs/start |
| kubectl | Kubernetes CLI | https://kubernetes.io/docs/tasks/tools |
| Git | Version control | https://git-scm.com/download/win |

---

## Configuration

The rate limiter is configured via environment variables, managed through a Kubernetes ConfigMap (`k8s/configmap.yaml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENDPOINT` | `/api/test` | The endpoint to apply rate limiting to |
| `MAX_REQUESTS_PER_SECOND` | `5` | Maximum allowed requests per second per IP |
| `REDIS_HOST` | `redis-service` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |

To change the configuration, edit `k8s/configmap.yaml` before deploying:
<img width="948" height="766" alt="image" src="https://github.com/user-attachments/assets/5a974aa5-f6d8-47c7-b138-4f175cf63911" />

```yaml
data:
  RATE_LIMIT_ENDPOINT: "/api/test"
  MAX_REQUESTS_PER_SECOND: "5"
```

---

## Deployment

### Local Testing with Docker Compose

Use Docker Compose to run the service locally before deploying to Kubernetes.

**1. Make sure Docker Desktop is running**

**2. Build and start the services:**
```bash
docker-compose up --build
```

**3. Verify the service is running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "redis": "connected"}
```

**4. Stop the services:**
```bash
docker-compose down
```

---

### Kubernetes Deployment

**1. Start Minikube:**
```bash
minikube start --driver=docker
```

**2. Point Docker to Minikube's Docker daemon (run in PowerShell):**
```powershell
minikube docker-env | Invoke-Expression
```

**3. Build the Docker image inside Minikube:**
```bash
docker build -t rate-limiter:latest .
```

**4. Apply all Kubernetes manifests:**
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/rate-limiter-deployment.yaml
```

**5. Verify all pods are running:**
```bash
kubectl get pods
```

Expected output:
```
NAME                            READY   STATUS    RESTARTS   AGE
rate-limiter-xxxxxxxxxx-xxxxx   1/1     Running   0          10s
redis-xxxxxxxxxx-xxxxx          1/1     Running   0          20s
```

**6. Get the service URL:**
```bash
minikube service rate-limiter-service --url
```

This returns a URL like `http://127.0.0.1:XXXXX`. Keep this terminal open and use this URL for all requests.

---

## Interacting with the Service

Replace `http://127.0.0.1:XXXXX` with the URL from the previous step.

### Test the rate-limited endpoint
```bash
curl http://127.0.0.1:XXXXX/api/test
```

Response when allowed (`200 OK`):
```json
{
  "status": "OK",
  "message": "Request accepted!",
  "ip": "10.244.0.1"
}
```

Response when rate limited (`429 Too Many Requests`):
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Max 5 requests/second allowed.",
  "ip": "10.244.0.1"
}
```

### Test rate limiting (send 10 requests rapidly)

**PowerShell:**
```powershell
for ($i=1; $i -le 10; $i++) { curl http://127.0.0.1:XXXXX/api/test -UseBasicParsing }
```

**Linux/Mac:**
```bash
for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:XXXXX/api/test; done
```

Expected: first 5 requests return `200`, remaining return `429`.

### Check service health
```bash
curl http://127.0.0.1:XXXXX/health
```

Response:
```json
{"status": "healthy", "redis": "connected"}
```

### Check current configuration
```bash
curl http://127.0.0.1:XXXXX/config
```

Response:
```json
{
  "rate_limited_endpoint": "/api/test",
  "max_requests_per_second": 5,
  "redis_host": "redis-service",
  "redis_port": 6379
}
```

---

## API Reference

| Method | Endpoint | Description | Rate Limited |
|--------|----------|-------------|--------------|
| GET | `/api/test` | Test endpoint | ✅ Yes |
| GET | `/health` | Health check | ❌ No |
| GET | `/config` | View current config | ❌ No |

---

## Persistent State (Crash Recovery)

Rate limit state is stored in Redis, not in the application memory. This means:

- If the rate limiter service crashes and restarts, Redis still holds all IP request counts
- The service immediately resumes enforcing rate limits without any data loss
- Redis is configured with `appendonly yes` for data persistence

To verify crash recovery:
```bash
# 1. Delete the rate limiter pod (simulates a crash)
kubectl delete pod -l app=rate-limiter

# 2. Kubernetes automatically restarts it — check until Running
kubectl get pods

# 3. Test the service again — rate limiting still works
curl http://127.0.0.1:XXXXX/api/test
```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `kubectl get pods` | Check pod status |
| `kubectl logs <pod-name>` | View app logs |
| `kubectl describe pod <pod-name>` | Debug a pod |
| `minikube stop` | Stop the Kubernetes cluster |
| `kubectl delete -f k8s/` | Remove all deployed resources |
