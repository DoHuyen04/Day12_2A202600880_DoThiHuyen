# Deployment Information — Day 12 Lab

> **Student:** Đỗ Thị Huyền · **ID:** 2A202600880
> **Project:** KnowledgeBase RAG Agent (`06-lab-complete`) — productionized từ dự án Day 7
> **Branch deploy:** `day12-productionize-rag-agent`

---

## 🌐 Public URL

```
https://elegant-commitment-production-1ad4.up.railway.app
```

## ☁️ Platform

- [x] Railway
- [ ] Render
- [ ] GCP Cloud Run

> Builder: `DOCKERFILE` (xem `06-lab-complete/railway.toml`). Root directory: `06-lab-complete`.

---

## 🔑 Environment Variables đã set trên Railway

| Biến | Giá trị | Ghi chú |
|------|---------|---------|
| `PORT` | (Railway tự inject) | KHÔNG hardcode — start command dùng `${PORT}` |
| `AGENT_API_KEY` | (bí mật) | Key bảo vệ `/ask` — KHÔNG commit |
| `EMBEDDING_PROVIDER` | `mock` | `mock` (offline) / `local` / `openai` |
| `OPENAI_API_KEY` | (đã xoá) | Trống → dùng mock LLM, không tốn tiền |
| `TOP_K` | `3` | Số chunk truy hồi |
| `RATE_LIMIT_PER_MINUTE` | `20` | Giới hạn request/phút |
| `DAILY_BUDGET_USD` | `5.0` | Usage guard/ngày |
| `ENVIRONMENT` | `development` | (nên đổi `production`) |

> ⚠️ Chỉ commit `.env.example`. KHÔNG commit `.env.local`.

---

## 🧪 Test Commands & Kết quả LIVE (verified 12/06/2026)

> Thay `<YOUR_KEY>` bằng `AGENT_API_KEY` đã set trên Railway.

### 1. Health check (public)
```bash
curl https://elegant-commitment-production-1ad4.up.railway.app/health
```
```json
{"status":"ok","version":"1.0.0","knowledge_base":{"documents":16,"chunks":200,"embedder":"mock embeddings fallback"},...}   ✅ HTTP 200
```

### 2. Readiness check
```bash
curl https://elegant-commitment-production-1ad4.up.railway.app/ready
```
```json
{"ready":true,"chunks":200}   ✅ HTTP 200
```

### 3. Auth bắt buộc — KHÔNG key → 401
```bash
curl -X POST https://elegant-commitment-production-1ad4.up.railway.app/ask \
  -H "Content-Type: application/json" -d '{"question":"test"}'
```
```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}   ✅ HTTP 401
```

### 4. CÓ key → 200 (RAG: answer + sources)
```bash
curl -X POST https://elegant-commitment-production-1ad4.up.railway.app/ask \
  -H "X-API-Key: <YOUR_KEY>" -H "Content-Type: application/json" \
  -d '{"question":"What is a vector store?","top_k":2}'
```
```json
{"question":"What is a vector store?","answer":"(mock-rag) ...",
 "sources":[{"source":"...","score":0.34,"preview":"..."}],
 "model":"mock-rag-llm","timestamp":"..."}   ✅ HTTP 200
```

### 5. Rate limiting — >20 req/phút → 429
```bash
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST \
    https://elegant-commitment-production-1ad4.up.railway.app/ask \
    -H "X-API-Key: <YOUR_KEY>" -H "Content-Type: application/json" \
    -d "{\"question\":\"test $i\"}"
done
# → 20× "200" rồi "429"  ✅
```

---

## ✅ Tổng hợp verify

| Test | Local (docker compose) | Live (Railway) |
|------|------------------------|----------------|
| Image multi-stage < 500 MB | ✅ 240 MB | — |
| Knowledge base load | ✅ 16 docs / 200 chunks | ✅ 16 docs / 200 chunks |
| `GET /health` | ✅ 200 | ✅ 200 |
| `GET /ready` | ✅ 200 | ✅ 200 |
| `POST /ask` không key | ✅ 401 | ✅ 401 |
| `POST /ask` có key | ✅ 200 + sources | ✅ 200 + sources |
| Rate limiting | ✅ 20 → 429 | ✅ |
| JSON structured logging | ✅ | ✅ |
| `$PORT` expand (cloud) | ✅ (test PORT=9090) | ✅ (Railway PORT=8080) |

---

## 📸 Screenshots

- [ ] `screenshots/dashboard.png` — Railway deploy success
- [ ] `screenshots/health.png` — Response `/health` (có `knowledge_base`)
- [ ] `screenshots/ask.png` — `/ask` trả answer + sources
- [ ] `screenshots/ratelimit.png` — chuỗi 200…429

---

## 🚀 Deploy lại

Railway nối GitHub repo `DoHuyen04/Day12_2A202600880_DoThiHuyen`, root dir `06-lab-complete`.
RAG agent được deploy từ branch **`day12-productionize-rag-agent`**.

```bash
# Auto-deploy: push lên branch Railway đang theo dõi
git push

# Hoặc deploy thủ công từ local:
cd 06-lab-complete
railway up
railway domain
```

> Bug đã fix để deploy chạy: `$PORT` expansion (shell-form), `PYTHONPATH` cho `--user` packages,
> `MutableHeaders.pop` → `del`, `.dockerignore` không loại nhầm `data/*.md`.
