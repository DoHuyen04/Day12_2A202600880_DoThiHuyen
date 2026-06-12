# Deployment Information — Day 12 Lab

> **Student:** Đỗ Thị Huyền · **ID:** 2A202600880
> **Project:** Production AI Agent (`06-lab-complete`)

---

## 🌐 Public URL

```
https://elegant-commitment-production-1ad4.up.railway.app
```

## ☁️ Platform

- [x] Railway
- [ ] Render
- [ ] GCP Cloud Run

> Đánh dấu platform bạn dùng. Cấu hình deploy: `06-lab-complete/railway.toml` (Railway) hoặc `06-lab-complete/render.yaml` (Render).

---

## 🔑 Environment Variables đã set trên platform

| Biến | Mô tả | Ghi chú |
|------|-------|---------|
| `ENVIRONMENT` | `production` | |
| `PORT` | Platform tự inject | KHÔNG hardcode — start command dùng `$PORT` |
| `AGENT_API_KEY` | API key bảo vệ `/ask` | Đặt giá trị bí mật, KHÔNG commit |
| `JWT_SECRET` | Secret ký JWT | Đặt giá trị bí mật |
| `REDIS_URL` | `redis://...` | Redis add-on của platform |
| `RATE_LIMIT_PER_MINUTE` | `20` | Giới hạn request/phút mỗi user |
| `DAILY_BUDGET_USD` | `5.0` | Cost guard mỗi user/ngày |
| `LOG_LEVEL` | `INFO` | (tùy chọn) |

> ⚠️ Chỉ commit `.env.example`. KHÔNG commit `.env` / `.env.local` chứa giá trị thật.

---

## 🧪 Test Commands

> Thay `<YOUR_KEY>` bằng `AGENT_API_KEY` đã set trên Railway.

### 1. Health check (public — không cần key)
```bash
curl https://elegant-commitment-production-1ad4.up.railway.app/health
# Actual: {"status":"ok","version":"1.0.0",...,"checks":{"llm":...}}  [HTTP 200] ✅
```

### 2. Readiness check
```bash
curl https://elegant-commitment-production-1ad4.up.railway.app/ready
# Actual: {"ready":true}  [HTTP 200] ✅
```

### 3. Auth bắt buộc — KHÔNG key → 401
```bash
curl -X POST https://elegant-commitment-production-1ad4.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
# Actual: {"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}  [HTTP 401] ✅
```

### 4. CÓ key → 200
```bash
curl -X POST https://elegant-commitment-production-1ad4.up.railway.app/ask \
  -H "X-API-Key: <YOUR_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is deployment?"}'
# Expected: HTTP 200 — {"question":"...","answer":"...","model":"...",...}
```

### 5. Rate limiting — gọi >20 lần/phút → 429
```bash
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST \
    https://elegant-commitment-production-1ad4.up.railway.app/ask \
    -H "X-API-Key: <YOUR_KEY>" -H "Content-Type: application/json" \
    -d "{\"question\":\"test $i\"}"
done
# Expected: 20× "200" rồi chuyển sang "429"
```

> **Đã verify live (12/06/2026):** `/health` → 200, `/ready` → 200, `/ask` không key → 401. ✅

---

## ✅ Kết quả test LOCAL (đã verify bằng docker compose)

Stack đã chạy thật trên máy (`docker compose up --build`) — image **247 MB** (< 500 MB):

| Test | Kết quả |
|------|---------|
| `GET /health` | ✅ 200 `{"status":"ok","version":"1.0.0",...}` |
| `GET /ready` | ✅ 200 `{"ready":true}` |
| `POST /ask` (không key) | ✅ 401 |
| `POST /ask` (có key) | ✅ 200 — trả lời từ mock LLM |
| Rate limiting | ✅ 20× 200 → 429 |
| Mô phỏng cloud `PORT=9090` | ✅ 200 (`$PORT` expand đúng) |
| JSON structured logging | ✅ `{"event":"request","status":...}` |

> Sau khi deploy lên cloud, chạy lại các lệnh ở mục "Test Commands" và dán kết quả vào đây.

---

## 📸 Screenshots

> Tạo thư mục `screenshots/` và thêm ảnh, rồi cập nhật link:

- [ ] `screenshots/dashboard.png` — Deployment dashboard (build success)
- [ ] `screenshots/running.png` — Service đang chạy / logs
- [ ] `screenshots/health.png` — Response `/health` từ public URL
- [ ] `screenshots/test.png` — Kết quả test auth + rate limit

---

## 🚀 Hướng dẫn deploy lại (Railway)

```bash
# 1. Commit & push code đã fix lên GitHub
git add 06-lab-complete/
git commit -m "fix lab06 deployment issues"
git push

# 2. Deploy
cd 06-lab-complete
npm i -g @railway/cli
railway login
railway init
railway variables set AGENT_API_KEY=<secret> JWT_SECRET=<secret> ENVIRONMENT=production
railway up
railway domain        # lấy public URL → điền vào đầu file này
```

> Lưu ý: deploy lấy code từ GitHub/CLI, nên **phải commit + push các fix trước** (Dockerfile, railway.toml, app/main.py, utils/) — nếu không sẽ gặp lại lỗi `$PORT is not a valid integer`.
