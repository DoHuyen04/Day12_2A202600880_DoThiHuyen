# Day 12 Lab — Mission Answers

> **Student Name:** Đỗ Thị Huyền
> **Student ID:** 2A202600880
> **Date:** 12/06/2026
> **Course:** AICB-P1 · VinUniversity 2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns tìm được trong `01-localhost-vs-production/develop/app.py`

Đọc file `develop/app.py`, tìm được **7 vấn đề** (yêu cầu tối thiểu 5):

1. **Hardcode secrets trong code** — `OPENAI_API_KEY = "sk-hardcoded-..."` và `DATABASE_URL` chứa user/password ngay trong source. Push lên GitHub là lộ key ngay lập tức.
2. **Không có config management** — `DEBUG = True`, `MAX_TOKENS = 500` cứng trong code, không đổi được giữa dev/staging/prod mà không sửa code.
3. **Dùng `print()` thay vì logging chuẩn** — và tệ hơn là `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` → **log cả secret ra console/log file**.
4. **Không có health check endpoint** — agent crash thì platform (Railway/Render/K8s) không biết để restart.
5. **Port cố định, không đọc từ env** — `port=8000` hardcode; trên cloud `PORT` được inject qua env var nên app sẽ không nhận traffic.
6. **Bind vào `host="localhost"`** — chỉ nhận kết nối nội bộ; trong container phải bind `0.0.0.0` mới nhận request từ ngoài.
7. **Bật `reload=True` (debug reload) trong production** — tốn tài nguyên, không an toàn, không nên dùng khi chạy thật.

> Bonus: không có graceful shutdown (không xử lý SIGTERM) và không validate input `question`.

---

### Exercise 1.3: Bảng so sánh Basic (develop) vs Advanced (production)

| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---------|-----------------|------------------------|---------------------|
| **Config** | Hardcode (`OPENAI_API_KEY`, `DEBUG`, port trong code) | Đọc từ env vars qua `config.py` (`Settings` dataclass + `os.getenv`) | 12-Factor: config tách khỏi code → đổi môi trường không cần sửa/build lại; không lộ secret trong git |
| **Health check** | ❌ Không có | ✅ `/health` (liveness), `/ready` (readiness), `/metrics` | Platform biết khi nào restart container; load balancer biết khi nào route traffic |
| **Logging** | `print()` thô, **log cả secret** | JSON structured logging, không log secret, có event/field rõ ràng | Dễ parse trong log aggregator (Datadog, Loki); không rò rỉ thông tin nhạy cảm |
| **Shutdown** | Đột ngột (không handle signal) | Graceful — handle `SIGTERM`, lifespan finish in-flight requests | Không cắt ngang request đang xử lý khi deploy/scale → không mất dữ liệu, không lỗi 5xx |
| **Host binding** | `localhost` (chỉ local) | `0.0.0.0` (chạy được trong container) | Container/cloud cần bind mọi interface mới nhận được traffic |
| **Port** | Cứng `8000` | Từ `PORT` env var | Railway/Render/Cloud Run inject PORT động |
| **CORS** | ❌ Không có | ✅ `CORSMiddleware` với `allowed_origins` cấu hình được | Kiểm soát origin nào được gọi API |
| **Validation** | ❌ Không check input | ✅ `raise HTTPException(422)` nếu thiếu `question` | Fail rõ ràng thay vì lỗi mơ hồ |
| **Fail fast** | Không | `settings.validate()` raise lỗi nếu thiếu `AGENT_API_KEY` ở production | Phát hiện cấu hình sai ngay lúc khởi động, không để chạy ngầm rồi lỗi sau |

### Checkpoint 1
- [x] Hiểu tại sao hardcode secrets là nguy hiểm (lộ qua git, log)
- [x] Biết cách dùng environment variables (`os.getenv` + `config.py` singleton)
- [x] Hiểu vai trò health check endpoint (liveness/readiness probe)
- [x] Biết graceful shutdown là gì (handle SIGTERM, finish in-flight requests)

---

## Part 2: Docker Containerization

### Exercise 2.1: Câu hỏi về `02-docker/develop/Dockerfile`

1. **Base image là gì?** → `python:3.11` — full Python distribution (~1 GB), kèm sẵn build tools.
2. **Working directory là gì?** → `/app` (đặt bằng `WORKDIR /app`).
3. **Tại sao COPY requirements.txt trước?** → Tận dụng **Docker layer cache**. Layer cài dependencies chỉ rebuild khi `requirements.txt` đổi. Nếu chỉ sửa code (`app.py`) thì Docker dùng lại layer dependencies đã cache → build nhanh hơn nhiều.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `CMD` = lệnh mặc định, **có thể bị override** khi `docker run image <lệnh khác>`.
   - `ENTRYPOINT` = lệnh cố định luôn chạy; tham số `docker run` được **append vào** entrypoint thay vì thay thế.
   - Thường dùng `ENTRYPOINT` cho executable cố định + `CMD` cho tham số mặc định. File này dùng `CMD ["python", "app.py"]` cho đơn giản, linh hoạt override.

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)

- **Stage 1 (`builder`) làm gì?** → Dùng `python:3.11-slim`, cài build tools (`gcc`, `libpq-dev`), rồi `pip install --user` toàn bộ dependencies vào `/root/.local`. Stage này **không dùng để deploy**.
- **Stage 2 (`runtime`) làm gì?** → Dùng `python:3.11-slim` sạch, tạo **non-root user** (`appuser`), `COPY --from=builder` chỉ phần packages đã cài + source code, set PATH/PYTHONPATH, thêm `HEALTHCHECK`, chạy bằng `uvicorn` với 2 workers.
- **Tại sao image nhỏ hơn?** → Image cuối **không chứa** build tools (gcc, apt cache, libpq-dev) và các file trung gian khi compile. Chỉ giữ runtime + site-packages cần thiết → nhỏ, sạch, ít bề mặt tấn công.

### Exercise 2.3: So sánh kích thước image (ước tính)

| Image | Base | Kích thước ước tính |
|-------|------|---------------------|
| **Develop** | `python:3.11` (full) single-stage | ~1.0 GB |
| **Production** | `python:3.11-slim` multi-stage | < 500 MB (mục tiêu, thường ~200–250 MB) |
| **Khác biệt** | | giảm ~60–75% |

> Lệnh kiểm tra thực tế: `docker images | grep my-agent` sau khi build hai image.

### Exercise 2.4: Docker Compose stack — Architecture

`02-docker/production/docker-compose.yml` định nghĩa **4 services** trong network `internal` (bridge):

```
                 Internet
                     │  (port 80/443)
                     ▼
            ┌─────────────────┐
            │  nginx (LB +    │  ← reverse proxy, rate limit, security headers
            │  reverse proxy) │
            └────────┬────────┘
                     │  http://agent_backend (round-robin)
                     ▼
            ┌─────────────────┐
            │   agent (FastAPI)│  ← KHÔNG expose port ra ngoài, chỉ qua nginx
            └───┬─────────┬────┘
                │         │
        ┌───────▼──┐  ┌───▼────────┐
        │  redis   │  │  qdrant    │
        │ (cache/  │  │ (vector DB │
        │  rate)   │  │  cho RAG)  │
        └──────────┘  └────────────┘
```

- **Services start:** `nginx`, `agent`, `redis`, `qdrant`.
- **Cách communicate:** qua **service name** trong network nội bộ (`redis://redis:6379`, `http://qdrant:6333`, nginx upstream `agent:8000`). Chỉ `nginx` expose port 80/443 ra ngoài; `agent` ẩn sau nginx.
- **Healthcheck + depends_on:** agent chỉ start khi `redis` và `qdrant` đã `service_healthy`. Có `restart: unless-stopped` và volumes (`redis_data`, `qdrant_data`) để persist dữ liệu.

### Checkpoint 2
- [x] Hiểu cấu trúc Dockerfile (FROM → WORKDIR → COPY req → RUN install → COPY code → CMD)
- [x] Biết lợi ích multi-stage builds (image nhỏ, không chứa build tools, non-root)
- [x] Hiểu Docker Compose orchestration (4 services, internal network, healthcheck, depends_on)
- [x] Biết debug container (`docker logs`, `docker exec -it <id> /bin/sh`)

---

## Part 3: Cloud Deployment

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| Khía cạnh | `railway.toml` | `render.yaml` |
|-----------|----------------|----------------|
| **Builder** | `NIXPACKS` (auto-detect Python, hoặc Dockerfile nếu có) | `runtime: python` + `buildCommand: pip install -r requirements.txt` |
| **Start command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| **Health check** | `healthcheckPath = "/health"`, timeout 30s | `healthCheckPath: /health` |
| **Auto-deploy** | (mặc định khi push) | `autoDeploy: true` |
| **Restart policy** | `ON_FAILURE`, max 3 retries | (Render quản lý ngầm) |
| **Env vars / secrets** | Set qua CLI/Dashboard (`railway variables set`) | Khai báo trong `envVars`; `sync: false` = set thủ công, `generateValue: true` = Render tự sinh |
| **Managed add-ons** | Không khai báo trong file (thêm qua dashboard) | Khai báo trực tiếp: service `type: redis` (Redis add-on) |
| **Region** | Chọn qua dashboard | `region: singapore` trong file |
| **Format** | TOML | YAML |

**Khác biệt chính:** `render.yaml` là **Infrastructure-as-Code đầy đủ hơn** — khai báo cả Redis add-on, region, env var generation trong 1 file (Blueprint). `railway.toml` tối giản hơn, tập trung vào build/deploy/health, còn lại để dashboard/CLI quản lý.

### Exercise 3.3: GCP Cloud Run CI/CD (`cloudbuild.yaml` + `service.yaml`)

**`cloudbuild.yaml` — pipeline 4 bước (CI/CD):**
1. **test** — `pip install` + `pytest tests/`.
2. **build** — `docker build` tag theo `$COMMIT_SHA` + `latest`, dùng `--cache-from` để cache layer. `waitFor: [test]`.
3. **push** — push image lên Container Registry (`gcr.io`). `waitFor: [build]`.
4. **deploy** — `gcloud run deploy` lên Cloud Run: region `asia-southeast1`, `--allow-unauthenticated`, `min-instances=1` (tránh cold start), `max-instances=10`, 512Mi/1cpu, secret lấy từ Secret Manager. `waitFor: [push]`.

**`service.yaml` — Cloud Run service definition (Knative IaC):**
- Scaling: `minScale=1`, `maxScale=10`, `containerConcurrency=80`.
- Resources: limit 1 cpu/512Mi, request 0.5 cpu/256Mi.
- Secrets từ Secret Manager (`OPENAI_API_KEY`, `AGENT_API_KEY`) — không hardcode.
- `livenessProbe` → `/health`; `startupProbe` → `/ready`.

### Checkpoint 3
- [x] Hiểu cấu hình deploy của 3 platform (Railway/Render/Cloud Run)
- [x] Hiểu cách set environment variables / secrets trên cloud
- [x] Hiểu CI/CD pipeline (test → build → push → deploy)
- [ ] Deploy thực tế lên platform → xem `DEPLOYMENT.md` (cần thực hiện khi nộp)

---

## Part 4: API Security

### Exercise 4.1: API Key authentication (`04-api-gateway/develop/app.py`)

- **API key được check ở đâu?** → Trong dependency `verify_api_key()` (đọc header `X-API-Key` qua `APIKeyHeader`), inject vào `/ask` bằng `Depends(verify_api_key)`. So sánh với `API_KEY = os.getenv("AGENT_API_KEY", ...)`.
- **Nếu sai/thiếu key?**
  - Thiếu key → **401 Unauthorized** ("Missing API key").
  - Sai key → **403 Forbidden** ("Invalid API key").
- **Làm sao rotate key?** → Đổi giá trị env var `AGENT_API_KEY` (trên dashboard/CLI) rồi restart/redeploy — không cần sửa code. Production tốt hơn nên hỗ trợ nhiều key cùng lúc (old + new) để rotate không downtime.

**Kết quả test mong đợi:**
```bash
# Không có key → 401
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

# Có key đúng → 200
{"question":"Hello","answer":"<mock response>"}
```

### Exercise 4.2: JWT authentication (`04-api-gateway/production/auth.py`)

**JWT flow:**
1. `POST /auth/token` với username/password → `authenticate_user()` kiểm tra `DEMO_USERS` → `create_token()` tạo JWT ký bằng `HS256`, chứa `sub` (user), `role`, `iat`, `exp` (hết hạn sau 60 phút).
2. Client gửi `Authorization: Bearer <token>` ở các request sau.
3. `verify_token()` decode + verify signature → trả `{username, role}`. **Stateless** — không cần query DB mỗi request.
4. Lỗi: thiếu token → 401; token hết hạn → 401 ("Token expired"); token sai → 403 ("Invalid token").

> Lưu ý: `DEMO_USERS` có `student` (role user, limit 50/ngày) và `teacher` (role admin, limit 1000/ngày). Secret từ env `JWT_SECRET`.

### Exercise 4.3: Rate limiting (`04-api-gateway/production/rate_limiter.py`)

- **Algorithm?** → **Sliding Window Counter**. Mỗi user có một `deque` chứa timestamp các request; loại bỏ timestamp cũ hơn `window_seconds` mỗi lần check.
- **Limit là bao nhiêu?** → User: **10 req/60s**; Admin: **100 req/60s** (hai instance singleton riêng).
- **Vượt limit?** → Raise **429 Too Many Requests** kèm header `X-RateLimit-Limit`, `X-RateLimit-Remaining: 0`, `X-RateLimit-Reset`, `Retry-After` và `retry_after_seconds` tính từ timestamp cũ nhất.
- **Bypass cho admin?** → Dùng `rate_limiter_admin` (limit cao 100/phút) dựa trên `role` trong JWT, thay vì `rate_limiter_user`.

**Kết quả test mong đợi:** gọi 20 lần liên tục → 10 request đầu trả 200, từ request thứ 11 trả **429**.

### Exercise 4.4: Cost guard (`04-api-gateway/production/cost_guard.py`)

**Cách tiếp cận trong code:**
- `CostGuard` theo dõi usage **theo ngày** per-user (`UsageRecord`: input/output tokens, request_count, day) + một **global budget**.
- `check_budget(user_id)` gọi **trước** khi gọi LLM:
  - Global cost ≥ `$10/ngày` → **503** (service tạm ngừng).
  - Per-user cost ≥ `$1/ngày` → **402 Payment Required**.
  - Đạt 80% budget → log warning.
- `record_usage()` gọi **sau** khi LLM trả về, cộng dồn tokens và tính cost theo giá GPT-4o-mini (`$0.15/1M` input, `$0.60/1M` output).
- Reset theo ngày tự động (so sánh `record.day` với ngày hiện tại).

**Implement bản Redis-backed (theo yêu cầu CODE_LAB — budget $10/tháng):**
```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    """Return True nếu còn budget, False nếu vượt $10/tháng."""
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False

    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # tự hết hạn sau ~1 tháng
    return True
```
> Dùng Redis thay in-memory để **state dùng chung giữa nhiều instance** khi scale (xem Part 5).

### Checkpoint 4
- [x] Hiểu & implement API key authentication (401/403)
- [x] Hiểu JWT flow (stateless, signature, expiry, role)
- [x] Implement rate limiting (sliding window, 429, header chuẩn)
- [x] Implement cost guard (per-user + global budget, Redis-backed)

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks (`05-scaling-reliability/develop/app.py`)

- **`/health` (Liveness)** — "agent còn sống không?". Trả `status: ok/degraded`, uptime, version, và check dependency (memory qua `psutil`). Non-200 → platform restart container.
- **`/ready` (Readiness)** — "sẵn sàng nhận traffic chưa?". Trả 503 khi đang startup/shutdown hoặc Redis chưa connect; 200 + `in_flight_requests` khi sẵn sàng. Load balancer dùng để quyết định route traffic.

Bản production (`production/app.py`) `/health` còn ping Redis và trả `status: degraded` nếu Redis mất kết nối; `/ready` raise 503 nếu Redis không ping được.

### Exercise 5.2: Graceful shutdown

- Đăng ký `signal.signal(SIGTERM/SIGINT, handle_sigterm)` để log; uvicorn tự bắt SIGTERM và gọi **lifespan shutdown**.
- Trong lifespan shutdown: set `_is_ready = False` (ngừng nhận traffic mới qua `/ready`), rồi **chờ `_in_flight_requests` về 0** (tối đa 30s) trước khi thoát.
- `_in_flight_requests` được đếm bằng middleware `track_requests` (++ khi vào, -- khi xong).
- Chạy `uvicorn(..., timeout_graceful_shutdown=30)` để cho phép finish request đang xử lý.

**Kết quả test:** gửi request "Long task" rồi `kill -TERM` ngay → request **vẫn hoàn thành** trước khi process thoát (thấy log "Waiting for N in-flight requests..." → "Shutdown complete").

### Exercise 5.3: Stateless design (`05-scaling-reliability/production/app.py`)

- **Anti-pattern:** lưu `conversation_history = {}` trong memory → khi scale nhiều instance, mỗi instance có memory riêng → user request 2 trúng instance khác là **mất history**.
- **Correct (trong code):** mọi session/history lưu trong **Redis** qua `save_session()/load_session()/append_to_history()` với key `session:{session_id}` và TTL 1h. Bất kỳ instance nào cũng đọc được session.
- Response trả `served_by: INSTANCE_ID` để chứng minh request được phục vụ bởi instance bất kỳ mà state vẫn đúng.
- Có fallback in-memory khi không có Redis (kèm cảnh báo "not scalable!") — chỉ để demo local.

### Exercise 5.4: Load balancing

- `docker compose up --scale agent=3` → 3 instance agent.
- **Nginx** (upstream `agent_backend`) round-robin phân tán request giữa các instance; `keepalive 32`. Nếu 1 instance die, traffic chuyển sang instance còn lại.
- Vì stateless (state ở Redis), scale ngang không làm hỏng conversation.

### Exercise 5.5: Test stateless (`test_stateless.py`)

Script: (1) tạo conversation qua nhiều request, (2) quan sát field `served_by` thay đổi giữa các instance, (3) history vẫn liên tục vì lưu ở Redis → chứng minh thiết kế stateless hoạt động khi scale.

### Checkpoint 5
- [x] Implement health (`/health`) và readiness (`/ready`) checks
- [x] Implement graceful shutdown (SIGTERM + chờ in-flight requests)
- [x] Refactor stateless (session/history trong Redis)
- [x] Hiểu load balancing với Nginx (round-robin, scale agent=3)
- [x] Test stateless design (`served_by` + history giữ nguyên)

---

## Part 6: Final Project — Lab 06 Complete

Project hoàn chỉnh nằm tại `06-lab-complete/` (chấm theo rubric 100 điểm).

### Checklist Non-functional (theo `06-lab-complete/`)
- [x] Dockerized multi-stage build (`Dockerfile`, mục tiêu < 500 MB)
- [x] Config từ environment variables (`app/config.py`)
- [x] API key authentication (`app/auth.py`)
- [x] Rate limiting 10 req/min per user (`app/rate_limiter.py`)
- [x] Cost guard $10/month per user (`app/cost_guard.py`)
- [x] Health check `/health` + readiness `/ready` (`app/main.py`)
- [x] Graceful shutdown (SIGTERM, lifespan)
- [x] Stateless design (state trong Redis)
- [x] Structured JSON logging
- [x] Deploy config Railway (`railway.toml`) + Render (`render.yaml`)
- [ ] Public URL hoạt động → ghi trong `DEPLOYMENT.md`

### Validation
```bash
cd 06-lab-complete
python check_production_ready.py
```
Script kiểm tra: Dockerfile valid + multi-stage, `.dockerignore`, `/health` & `/ready` trả 200, auth bắt buộc (401 không key), rate limit (429), cost guard (402), graceful shutdown, stateless (Redis), JSON logging.

---

## Tổng kết

Đã hoàn thành đọc hiểu và trả lời toàn bộ bài tập Part 1–6. Phần còn lại cần thực hiện khi nộp:
1. Deploy Lab 06 lên Railway/Render → lấy **public URL** → điền vào `DEPLOYMENT.md`.
2. Chụp screenshot deployment dashboard + test results → thư mục `screenshots/`.
3. Chạy `check_production_ready.py` để xác nhận tất cả check pass.
