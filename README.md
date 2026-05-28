Rate Limiter Service

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
<img width="984" height="610" alt="image" src="https://github.com/user-attachments/assets/bb15afda-88d0-484b-9e30-5cb9d8d3a1ce" />

**3. Verify the service is running:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "redis": "connected"}
```
<img width="1105" height="585" alt="image" src="https://github.com/user-attachments/assets/ed18beec-b3c8-4c9e-8aa8-d5d102281c74" />

**4. Stop the services:**
```bash
docker-compose down
```
<img width="1205" height="176" alt="image" src="https://github.com/user-attachments/assets/a88cddc8-645a-4715-b27d-7277dcf5f90c" />

---

### Kubernetes Deployment

**1. Start Minikube:**
```bash
minikube start --driver=docker
```
<img width="933" height="275" alt="image" src="https://github.com/user-attachments/assets/2470af00-1b02-48ad-961f-e9932061445b" />


**2. Point Docker to Minikube's Docker daemon (run in PowerShell):**
```powershell
minikube docker-env | Invoke-Expression
```

**3. Build the Docker image inside Minikube:**
```bash
docker build -t rate-limiter:latest .
```
<img width="1009" height="540" alt="image" src="https://github.com/user-attachments/assets/c77a7fc1-c730-4619-a434-dae55a446896" />


**4. Apply all Kubernetes manifests:**
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/rate-limiter-deployment.yaml
```
<img width="988" height="233" alt="image" src="https://github.com/user-attachments/assets/59f0a46d-eb10-45ae-8c63-ff6e84350002" />


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
<img width="845" height="116" alt="image" src="https://github.com/user-attachments/assets/02ba14d9-2479-44dc-80d9-1f676d7ea5fc" />

**6. Get the service URL:**
```bash
minikube service rate-limiter-service --url
```
<img width="1049" height="141" alt="image" src="https://github.com/user-attachments/assets/332f1f1e-d1b1-451d-bc9f-8d7fa7a5be5e" />

This returns a URL like `http://127.0.0.1:XXXXX`. Keep this terminal open and use this URL for all requests.

---
<img width="1135" height="442" alt="image" src="https://github.com/user-attachments/assets/2d07ca3c-c1df-4623-bbd9-32c4d9d27236" />
<img width="1149" height="397" alt="image" src="https://github.com/user-attachments/assets/ef4fa285-d984-4f98-a6d6-7d32f7701659" />
<img width="1138" height="434" alt="image" src="https://github.com/user-attachments/assets/64444441-36a3-4ea7-8a8d-c6a26ed0f00a" />


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
<img width="1107" height="353" alt="image" src="https://github.com/user-attachments/assets/54e21d13-75c8-445a-b2e0-595573b26272" />

Response when rate limited (`429 Too Many Requests`):
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Max 5 requests/second allowed.",
  "ip": "10.244.0.1"
}
```
<img width="1016" height="493" alt="image" src="https://github.com/user-attachments/assets/9bc60255-2dfd-4889-bb85-4e4753fdb3f7" />

### Test rate limiting (send 10 requests rapidly)

**PowerShell:**
```powershell
for ($i=1; $i -le 10; $i++) { curl http://127.0.0.1:XXXXX/api/test -UseBasicParsing }
```
<img width="1195" height="709" alt="image" src="https://github.com/user-attachments/assets/f6343bfd-a826-45cc-a734-fdafa9ef4cb5" />

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
