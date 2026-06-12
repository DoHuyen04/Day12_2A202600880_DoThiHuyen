# Lab 12 — Production RAG Agent (KnowledgeBaseAgent)

> **Student:** Đỗ Thị Huyền · **ID:** 2A202600880
> Dự án cá nhân **Day 7 — KnowledgeBaseAgent (RAG)** được **productionize** theo các bước Day 12.

RAG agent trả lời câu hỏi dựa trên cơ sở tri thức: truy hồi top-k chunk liên quan
từ vector store rồi sinh câu trả lời **chỉ dựa trên context** (kèm nguồn).

---

## Productionization Checklist

- [x] Dockerfile multi-stage (< 500 MB, image ~240 MB)
- [x] docker-compose.yml
- [x] .dockerignore
- [x] Config từ environment variables (`app/config.py`)
- [x] API Key authentication (`X-API-Key`)
- [x] Rate limiting (sliding window, 20 req/min)
- [x] Cost/usage guard (per-day budget)
- [x] Health check `GET /health` + Readiness `GET /ready`
- [x] Graceful shutdown (SIGTERM, lifespan)
- [x] Structured JSON logging
- [x] Knowledge base load lúc startup
- [x] Deploy config: `railway.toml` + `render.yaml`

---

## Cấu trúc

```
06-lab-complete/
├── app/
│   ├── main.py            # FastAPI app: /ask /health /ready /metrics
│   ├── config.py          # 12-factor config (env vars)
│   ├── llm.py             # LLM backend (mock | openai)
│   ├── knowledge_base.py  # Load docs → build store + agent (startup)
│   └── rag/               # Agent gốc Day 7 (giữ nguyên logic)
│       ├── agent.py       # KnowledgeBaseAgent (retrieve → prompt → LLM)
│       ├── store.py       # EmbeddingStore (vector store in-memory)
│       ├── embeddings.py  # Mock / Local / OpenAI embedder
│       ├── chunking.py    # ParagraphChunker, ...
│       └── models.py      # Document
├── data/                  # Knowledge base (.md / .txt)
├── Dockerfile             # Multi-stage, non-root, HEALTHCHECK
├── docker-compose.yml
├── railway.toml / render.yaml
├── requirements.txt
├── .env.example
└── check_production_ready.py
```

---

## Chạy Local

```bash
cp .env.example .env.local
docker compose up --build

# Health
curl http://localhost:8000/health

# Hỏi agent (cần API key)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question":"Vector store dung de lam gi?","top_k":3}'
```

Response gồm `answer` + `sources` (file nguồn, score, preview).

---

## Cấu hình (env vars)

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `PORT` | 8000 | Cloud tự inject |
| `AGENT_API_KEY` | (bắt buộc ở prod) | Key bảo vệ `/ask` |
| `EMBEDDING_PROVIDER` | `mock` | `mock` (offline) / `local` / `openai` |
| `OPENAI_API_KEY` | (trống) | Có key → dùng OpenAI; trống → mock LLM |
| `TOP_K` | 3 | Số chunk truy hồi |
| `CHUNK_MAX_CHARS` | 700 | Kích thước chunk |
| `RATE_LIMIT_PER_MINUTE` | 20 | Giới hạn request/phút |
| `DAILY_BUDGET_USD` | 5.0 | Ngân sách/ngày |

> Mặc định chạy **offline hoàn toàn** (mock embeddings + mock LLM) — không cần API key, không tốn tiền.

---

## Deploy

```bash
# Railway
railway up
railway variables set AGENT_API_KEY=<secret> ENVIRONMENT=production
railway domain
```

Xem URL đã deploy + lệnh test trong [`../DEPLOYMENT.md`](../DEPLOYMENT.md).

---

## Kiểm tra Production Readiness

```bash
python check_production_ready.py   # 20/20 ✅
```
