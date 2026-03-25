# AI Code Reviewer

Current progress:
- Step 1: FastAPI scaffold + `/review`
- Step 2: AI integration (OpenAI or Anthropic)
- Step 3: Parsing + schema validation
- Step 4: React + Monaco frontend scaffold
- Step 5: Issue rendering + severity colors + editor line highlights
- Step 6: Integration hardening (timeouts, retries, input limits, CORS env config)
- Step 7: Deployment config for Railway (backend) + Vercel (frontend)

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend default URL: `http://localhost:5173`
Backend default URL: `http://127.0.0.1:8000`

## Backend Environment Variables

- `MODEL_PROVIDER`: `openai` or `anthropic`
- `MODEL_NAME`: provider model id
- `OPENAI_API_KEY`: required if `MODEL_PROVIDER=openai`
- `ANTHROPIC_API_KEY`: required if `MODEL_PROVIDER=anthropic`
- `REQUEST_TIMEOUT_SECONDS`: timeout per provider request
- `AI_MAX_RETRIES`: retry count on transient AI errors
- `MAX_CODE_LINES`: backend line limit
- `MAX_CODE_CHARS`: backend character limit
- `MOCK_MODE`: `true` for offline/demo mode, `false` for live AI
- `CORS_ORIGINS`: comma-separated allowed frontend origins

## Frontend Environment Variables

- `VITE_API_BASE_URL`: backend base URL
- `VITE_API_TIMEOUT_MS`: request timeout in milliseconds
- `VITE_API_MAX_RETRIES`: retry count for retryable API failures

## Deployment (Step 7)

### Deploy Backend to Railway

1. Push repo to GitHub.
2. In Railway, create a new project from the repo.
3. Set service root directory to `backend`.
4. Railway will use `backend/railway.json` (and `backend/Procfile` fallback).
5. Configure backend environment variables in Railway.

Recommended production backend env:

```env
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
REQUEST_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=2
MAX_CODE_LINES=500
MAX_CODE_CHARS=25000
MOCK_MODE=false
CORS_ORIGINS=https://your-frontend.vercel.app
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=
```

### Deploy Frontend to Vercel

1. Import the same GitHub repo in Vercel.
2. Set project root directory to `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Set frontend env variable:

```env
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_API_TIMEOUT_MS=20000
VITE_API_MAX_RETRIES=1
```

6. Redeploy frontend after setting env vars.
7. Update Railway `CORS_ORIGINS` with your final Vercel domain and redeploy backend.

## Post-Deployment Verification

1. Check backend health: `GET https://your-backend.railway.app/health`.
2. Open frontend app and run a code review.
3. Confirm findings render with severity colors and line highlights.
4. Confirm error handling by temporarily setting invalid API key.

## API Contract

`POST /review`

Request:

```json
{
  "code": "string",
  "language": "string"
}
```

Response:

```json
{
  "issues": [
    {
      "type": "bug",
      "line": 10,
      "severity": "high",
      "message": "description"
    }
  ]
}
```