# Team Report — 26S-27

> ProAgent · Intelligent Collaboration Workstation  
> <https://github.com/lsz-asd/team-project-26spring-26s-27>

---

## 1. Metrics

*Computed by `metrics_tool/metrics.py`.  Figures below are from the current integration branch and will be updated with the final commit.*

### 1.1 Lines of Code & Source Files

**Summary**

| Metric | Current | Final |
|--------|---------|-------|
| Source files | 261 | _______ |
| Physical lines | 48,379 | _______ |
| Code lines (excl. blanks & comments) | 41,167 | _______ |

**Breakdown by language**

| Language | Files | Total | Code | Blank |
|----------|-------|-------|------|-------|
| Python | 204 | 34,321 | 28,872 | 5,449 |
| Vue | 26 | 10,088 | 8,853 | 1,235 |
| JavaScript | 21 | 3,313 | 2,865 | 448 |
| Rust | 3 | 155 | 132 | 23 |
| SQL | 2 | 347 | 313 | 34 |
| CSS | 2 | 86 | 73 | 13 |
| TOML | 2 | 56 | 46 | 10 |
| HTML | 1 | 13 | 13 | 0 |

> *Above table will be regenerated with final project code.*

### 1.2 Cyclomatic Complexity (Python)

| Metric | Current | Final |
|--------|---------|-------|
| Average complexity | 3.9 | _______ |

**Distribution**

| Rating | Range | Functions |
|--------|-------|-----------|
| A | 1 – 5 | 1,327 |
| B | 6 – 10 | 212 |
| C | 11 – 20 | 82 |
| D | 21 – 30 | 18 |
| E | 31 – 40 | 2 |
| F | 41+ | 8 |

**Top 5 most complex functions**

| # | Function | File | CC |
|---|----------|------|----|
| 1 | `execute` | `localagent/tools/search.py` | 64 |
| 2 | `validate_sync_packet` | `local_backend/database/.../database_synchronize_operations.py` | 49 |
| 3 | `validate_sync_packet` | `server_backend/database/.../database_synchronize_operations.py` | 49 |
| 4 | `LocalSyncImporter` | `local_backend/database/.../database_synchronize_operations.py` | 47 |
| 5 | `apply_local_sync_json` | `local_backend/database/.../database_synchronize_operations.py` | 46 |

> *Above table will be regenerated with final project code.*

### 1.3 Dependencies

| Manifest | Runtime | Dev | Total |
|----------|---------|-----|-------|
| `frontend/package.json` | 8 | 6 | 14 |
| `local_backend/requirements.txt` | 19 | — | 19 |
| `server_backend/requirements.txt` | 12 | — | 12 |
| `example_backend/requirements.txt` | 18 | — | 18 |
| `frontend/src-tauri/Cargo.toml` | 7 | 1 | 8 |
| **Total (deduplicated)** | **43** | **7** | **50** |

| Summary metric | Current | Final |
|----------------|---------|-------|
| Total dependencies | 50 | _______ |

> *Above table will be regenerated with final project code.*

---

## 2. CI/CD Pipeline Description

### 2.1 Overview

The pipeline is a single GitHub Actions workflow (`.github/workflows/ci-cd.yml`) organized into **six stages** with **15 jobs**.  Jobs within a stage run in parallel; downstream stages wait on upstream ones via `needs`.  Artifacts (built frontend, coverage reports, packages, API docs) flow between stages through `actions/upload-artifact` / `actions/download-artifact`.

**Trigger:** `push` and `pull_request` to `main` and `integration`.

**Configuration:**  
<https://github.com/lsz-asd/team-project-26spring-26s-27/blob/integration/.github/workflows/ci-cd.yml>

### 2.2 Pipeline stages

#### Stage 1 — Compile

| Job | Runtime | What it does |
|-----|---------|--------------|
| `compile-local` | Python 3.10 | `pip install -r local_backend/requirements.txt` → `python -m compileall local_backend/` |
| `compile-server` | Python 3.10 | Same for `server_backend/` |
| `build-frontend` | Node.js 22 | `npm ci` → `npm run build` (Vite), uploads `frontend/dist/` artifact |

#### Stage 2 — Test

| Job | Runtime | Tools | What it does |
|-----|---------|-------|--------------|
| `lint` | Python 3.10 | flake8 | Lints both backends (`--max-line-length=120 --exit-zero`) |
| `test-local` | Python 3.10 | pytest, pytest-cov | Runs `local_backend/tests/` with coverage XML + HTML reports, uploads both as artifacts |
| `test-server` | Python 3.10 | pytest, pytest-cov | Same for `server_backend/tests/` |
| `test-frontend` | Node.js 22 | vitest | `npm run test` in `frontend/` |

#### Stage 3 — Package

| Job | Depends on | What it produces |
|-----|------------|------------------|
| `package-local` | compile-local, build-frontend, test-local, test-frontend | `proagent-local-<date>-<sha>.zip` containing `local_backend/`, `frontend/dist/`, launch scripts, `requirements.txt` |
| `package-server` | compile-server, test-server | `proagent-server-<date>-<sha>.zip` containing `server_backend/`, launch scripts, `requirements.txt` |

Both use `date-SHA` versioning.  Local package retained 30 days, server package retained 30 days.

#### Stage 4 — Docs

| Job | Depends on | Tools | Output |
|-----|------------|-------|--------|
| `gen-docs` | compile-local, compile-server | pdoc3 | HTML API docs for both backends, uploaded as `api-docs` artifact (30 days) |

#### Stage 5 — Docker

| Job | Condition | What it does |
|-----|-----------|--------------|
| `docker-build` | always | Builds `Dockerfile.local`, `Dockerfile.server`, `Dockerfile.frontend` |
| `docker-test` | always | `docker compose up -d` → health-check all three services → `docker compose down` |
| `docker-push` | only on push to main/integration | Pushes images to `ghcr.io/<owner>/proagent-*` |

#### Stage 6 — Kubernetes

| Job | Depends on | Tools | What it does |
|-----|------------|-------|--------------|
| `k8s-validate` | — | kubeconform | Validates manifests under `k8s/` |
| `k8s-test` | k8s-validate | kind, kubectl | Creates ephemeral kind cluster, loads Docker images, `kubectl apply -k k8s/`, waits for deployments, port-forwards for health checks, tears down |

### 2.3 Tool summary

| Purpose | Tool |
|---------|------|
| Orchestrator | GitHub Actions |
| Python testing + coverage | pytest 9.x, pytest-cov |
| Python linting | flake8 |
| Frontend testing | vitest 4.x |
| Frontend build | Vite 7 |
| Containerization | Docker, Docker Compose |
| Container registry | GitHub Container Registry (ghcr.io) |
| K8s manifest validation | kubeconform |
| K8s integration test | kind (Kubernetes IN Docker) |
| API documentation | pdoc3 |

### 2.4 Pipeline execution proof

*[TODO: Insert screenshot of a fully-passing CI/CD pipeline run from the GitHub Actions tab after final push.]*
