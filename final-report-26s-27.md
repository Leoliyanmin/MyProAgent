# Team Report — 26S-27

> ProAgent · Intelligent Collaboration Workstation  
> <https://github.com/sustech-cs304/team-project-26spring-26s-27>

---

## 1. Metrics

*Computed by `metrics_tool/metrics.py`.  Figures below are from the current integration branch.*

### 1.1 Lines of Code & Source Files

**Summary**

| Metric | Value |
|--------|-------|
| Source files | 261 |
| Physical lines | 48,379 |
| Code lines (excl. blanks & comments) | 41,167 |

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

### 1.2 Cyclomatic Complexity (Python)

| Metric | Value |
|--------|-------|
| Average complexity | 3.9 |

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

### 1.3 Dependencies

| Manifest | Runtime | Dev | Total |
|----------|---------|-----|-------|
| `frontend/package.json` | 8 | 6 | 14 |
| `local_backend/requirements.txt` | 19 | — | 19 |
| `server_backend/requirements.txt` | 12 | — | 12 |
| `example_backend/requirements.txt` | 18 | — | 18 |
| `frontend/src-tauri/Cargo.toml` | 7 | 1 | 8 |
| **Total (deduplicated)** | **43** | **7** | **50** |

---

## 2. CI/CD Pipeline Description

### 2.1 Overview

The pipeline is a single GitHub Actions workflow (`.github/workflows/ci-cd.yml`) organized into **eight stages** with **17 jobs**.  Jobs within a stage run in parallel; downstream stages wait on upstream ones via `needs`.  Artifacts (built frontend, coverage reports, packages, binary executables, API docs) flow between stages through `actions/upload-artifact` / `actions/download-artifact`.

**Trigger:** `push` and `pull_request` to `main`, `integration`, and `integration_mac`; `workflow_dispatch` with optional `tag` input for releases.

**Configuration:**  
<https://github.com/sustech-cs304/team-project-26spring-26s-27/blob/integration_mac/.github/workflows/ci-cd.yml>

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
| `lint` | Python 3.10 | flake8 | Lints both backends (`--max-line-length=120`, `.flake8` config for pre-existing violations) |
| `test-local` | Python 3.10 | pytest, pytest-cov | Runs `local_backend/tests/` with coverage XML + HTML reports, uploads both as artifacts |
| `test-server` | Python 3.10 | pytest, pytest-cov | Same for `server_backend/tests/` |
| `test-frontend` | Node.js 22 | vitest | `npm run test` in `frontend/` (22 tests, all passing) |

#### Stage 3 — Package

| Job | Depends on | Runtime | What it produces |
|-----|------------|---------|------------------|
| `package-local` | compile-local, build-frontend, test-local, test-frontend | ubuntu-latest | `proagent-local-<date>-<sha>.zip` containing `local_backend/`, `frontend/dist/`, launch scripts (`start.sh`, `start.bat`), `requirements.txt` |
| `package-server` | compile-server, test-server | ubuntu-latest | `proagent-server-<date>-<sha>.zip` containing `server_backend/`, launch scripts, `requirements.txt` |
| `package-server-macos` | test-server | macos-latest | macOS standalone binary `proagent-server-macos` built with PyInstaller, with smoke-test verification step |

All use `date-SHA` versioning.  Launch scripts are `chmod +x`-ed before zipping to preserve execute permissions on macOS.

#### Stage 4 — Docs

| Job | Depends on | Tools | Output |
|-----|------------|-------|--------|
| `gen-docs` | compile-local, compile-server | pdoc3 | HTML API docs for both backends, uploaded as `api-docs` artifact (30 days, `continue-on-error: true`) |

#### Stage 5 — Docker & GitHub Container Registry (GHCR)

| Job | Condition | What it does |
|-----|-----------|--------------|
| `docker-build` | always | Builds three images from `docker/Dockerfile.*`: `Dockerfile.local` (python:3.10-slim, port 8002), `Dockerfile.server` (python:3.10-slim, port 8001, with HEALTHCHECK), `Dockerfile.frontend` (multi-stage: node:22-alpine build → nginx:alpine serve, port 80, with HEALTHCHECK). Pushes to GHCR via PAT. |
| `docker-test` | always | `docker compose up -d` → health-check all three services with `condition: service_healthy` → `docker compose down` |

Images are pushed to `ghcr.io/leoliyanmin/proagent-*` using a Personal Access Token stored as `GHCR_PAT` secret. Builds use `--no-cache` to avoid partial blob issues from cancelled runs.

The three published GHCR packages are:

| Package | Full Path | Base Image |
|---------|-----------|------------|
| `proagent-local` | `ghcr.io/leoliyanmin/proagent-local:latest` | `python:3.10-slim` |
| `proagent-server` | `ghcr.io/leoliyanmin/proagent-server:latest` | `python:3.10-slim` |
| `proagent-frontend` | `ghcr.io/leoliyanmin/proagent-frontend:latest` | `node:22-alpine` → `nginx:alpine` |

#### Stage 6 — Kubernetes

| Job | Depends on | Tools | What it does |
|-----|------------|-------|--------------|
| `k8s-validate` | — | kubeconform | Validates manifests under `k8s/` |
| `k8s-test` | k8s-validate | kind, kubectl | Creates ephemeral kind cluster, builds and loads three Docker images (`ghcr.io/<owner>/proagent-*`), applies `kubectl apply -k k8s/`, waits for deployments with `imagePullPolicy: IfNotPresent`, port-forwards for health checks, tears down |

K8s manifests use `REPLACE_ME` placeholder which is sed-replaced with the owner at test time.  Environment variable `TEST_MODE` is set to `false` for secure defaults in Kubernetes deployments.

#### Stage 7 — GitHub Release (CD)

| Job | Condition | What it does |
|-----|-----------|--------------|
| `github-release` | tag push or `workflow_dispatch` | Downloads all artifacts (`proagent-local-*.zip`, `proagent-server-*.zip`, `proagent-server-macos`, `proagent-macos-dmg/*.dmg`), creates GitHub Release with auto-generated release notes via `softprops/action-gh-release@v2` |

#### Stage 8 — Tauri Desktop App Build

| Job | Runtime | Condition | What it does |
|-----|---------|-----------|--------------|
| `tauri-build` | ubuntu-22.04 | `github.actor == 'lsz-asd'` | Linux Tauri AppImage |
| `tauri-build-windows` | windows-latest | `github.actor == 'lsz-asd'` | Windows NSIS installer |
| `tauri-build-macos` | macos-latest | always | macOS DMG, builds Python sidecar with PyInstaller, uploads DMG for Release |

The macOS build bundles both `python-backend` (local API, port 8002) and `server-backend` (server API, port 8001) as Tauri sidecars, including persistent data directories at `~/Library/Application Support/proagent-*`. PyInstaller commands use comprehensive `--hidden-import` and `--collect-submodules` flags for `passlib`, `email`, `jose`, `cryptography`, `redis`, and others.

### 2.3 Tool summary

| Purpose | Tool |
|---------|------|
| Orchestrator | GitHub Actions |
| Python testing + coverage | pytest 9.x, pytest-cov |
| Python linting | flake8 (with `.flake8` config) |
| Frontend testing | vitest 4.x |
| Frontend build | Vite 7 |
| Containerization | Docker, Docker Compose |
| Container registry | GitHub Container Registry (ghcr.io) |
| K8s manifest validation | kubeconform |
| K8s integration test | kind (Kubernetes IN Docker) |
| Python binary packaging | PyInstaller |
| macOS desktop app | Tauri v2 |
| API documentation | pdoc3 |
| Release management | softprops/action-gh-release |

### 2.4 Pipeline execution proof

![Action1](resources/Action1.png)

![Action2](resources/Action2.png)

---

## 3. Key Design Decisions

### 3.1 Four-Layer Architecture
Both `local_backend` and `server_backend` follow a consistent four-layer pattern: **database → business → service → presentation**. This separation enables independent testing of each layer and parallel development across team members.

### 3.2 Local ↔ Server Synchronization
Data is synchronized bidirectionally between local and server backends via `/sync/from-client` and `/sync/to-client` endpoints. Sync intervals are configurable (default: 10s for local sync, 5s for email sync in demo mode). Each user maintains a monotonic `user_version` for conflict resolution.

### 3.3 Security
- Passwords hashed with **bcrypt** (unified across both backends via `passlib` with auto-upgrade from legacy `sha256_crypt`)
- API keys encrypted with **Fernet AES** symmetric encryption
- Personality/profile data encrypted at rest
- JWT token authentication with configurable expiry
- Email-based verification codes with 5-minute expiry and retry limits
- CORS middleware for cross-origin access control
- `TEST_MODE` default is `false` for secure production deployment; `.env` overrides for development

### 3.4 Persistent Data in PyInstaller Bundles
macOS PyInstaller bundles write to temporary directories that are deleted on exit. We resolved this by routing database, personality profiles, and interaction logs to `~/Library/Application Support/proagent-*/`. The `database_command.py` module's `DEFAULT_DB_PATH` is monkey-patched at startup to ensure all DB operations use the persistent path.

### 3.5 Agent Workspace Dynamics
The LocalAgent's workspace (file operations, session storage, memory) is dynamically switchable per request via the `working_directory` parameter. When a user selects a folder in the frontend, the agent's tool resolution base changes to that directory, allowing the AI to operate in the correct context.
