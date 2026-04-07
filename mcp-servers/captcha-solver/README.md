# CAPTCHA Solver MCP

Multi-strategy CAPTCHA solver for AI agents. Uses free local AI (CLIP + Gemini Vision) to solve CAPTCHAs -- no paid API key required.

**Drop-in replacement for 2Captcha and CapSolver** with a free tier that costs you nothing.

## Why This Solver?

| Feature | This Solver | 2Captcha | CapSolver |
|---------|------------|----------|-----------|
| Free tier | Yes (250 solves/day) | No | No |
| Local AI solving | Yes (CLIP) | No | No |
| MCP server | Yes | No | No |
| 2Captcha API compatible | Yes | - | No |
| CapSolver API compatible | Yes | No | - |
| hCaptcha image grids | Yes | Yes | Yes |
| hCaptcha canvas | Yes | No | No |
| reCAPTCHA v2 | Yes | Yes | Yes |
| reCAPTCHA v3 | Yes (via API) | Yes | Yes |
| Cloudflare Turnstile | Yes (via API) | Yes | Yes |

## How It Works

Smart routing tries the cheapest solver first:

```
CLIP (free, local) --> Gemini Vision (free, 250/day) --> External API (paid fallback)
```

- **CLIP**: Zero-shot image classification. Free, runs locally, no API key needed.
- **Gemini Vision**: Google's free VLM. Handles complex canvas challenges.
- **External API**: CapSolver or 2Captcha as last resort (requires their API key).

## Quick Start

### As MCP Server (for Claude Desktop, Cursor, etc.)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "captcha-solver": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### As REST API

```bash
# Install
pip install -r requirements.txt

# Set your keys
export GEMINI_API_KEY=your-key-here
export API_KEYS=your-client-key-here

# Run
uvicorn api:app --host 0.0.0.0 --port 8000
```

### With Docker

```bash
# VLM-only mode (lightweight, ~200MB image)
docker build --target vlm-only -t captcha-solver .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e API_KEYS=your-client-key \
  captcha-solver

# Full mode with CLIP (adds local AI, ~2GB image)
docker build --target full -t captcha-solver-full .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e API_KEYS=your-client-key \
  captcha-solver-full
```

## API Reference

### POST /solve

Solve a CAPTCHA directly. Returns result immediately.

```bash
curl -X POST http://localhost:8000/solve \
  -H "Authorization: Bearer your-client-key" \
  -H "Content-Type: application/json" \
  -d '{
    "task_text": "Please click each image containing a bus",
    "images": ["data:image/png;base64,...", "data:image/png;base64,..."],
    "captcha_type": "hcaptcha"
  }'
```

Response:
```json
{
  "success": true,
  "solver": "vlm",
  "selections": [0, 3, 7],
  "confidence": 0.75,
  "cost_usd": 0.0,
  "solve_time_ms": 3200
}
```

### POST /createTask (CapSolver compatible)

```bash
curl -X POST http://localhost:8000/createTask \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "your-client-key",
    "task": {
      "type": "HCaptchaTaskProxyLess",
      "websiteURL": "https://example.com",
      "websiteKey": "site-key-here"
    }
  }'
```

### POST /getTaskResult (CapSolver compatible)

```bash
curl -X POST http://localhost:8000/getTaskResult \
  -H "Content-Type: application/json" \
  -d '{
    "clientKey": "your-client-key",
    "taskId": "task-id-from-createTask"
  }'
```

### GET /health

No auth required. Returns `{"status": "ok"}`.

## Supported CAPTCHA Types

| Type | Solving Method | Notes |
|------|---------------|-------|
| hCaptcha image grids | CLIP / VLM | 3x3, 4x4 grids |
| hCaptcha canvas | VLM | Bucket, silhouette, line challenges |
| reCAPTCHA v2 | CLIP / VLM | Image selection |
| reCAPTCHA v3 | External API | Token-based (invisible) |
| Cloudflare Turnstile | External API | Token-based |
| FunCaptcha | VLM | 3D interactive puzzles |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Recommended | Free Gemini Vision (250 solves/day) |
| `API_KEYS` | Yes (for REST API) | Comma-separated client API keys |
| `RATE_LIMIT_RPM` | No | Requests per minute per key (default: 30) |
| `ANTHROPIC_API_KEY` | No | Claude Vision (~$0.004/solve) |
| `OPENAI_API_KEY` | No | GPT-4o Vision (~$0.002/solve) |
| `CAPSOLVER_API_KEY` | No | CapSolver fallback (~$0.002/solve) |
| `TWOCAPTCHA_API_KEY` | No | 2Captcha fallback (~$0.003/solve) |

## Performance

Tested with 50 concurrent requests on Gemini free tier:

| Metric | Result |
|--------|--------|
| Success rate | 100% (50/50) |
| Memory usage | 73MB peak (VLM-only mode) |
| Avg latency (1 req) | ~3-5s |
| Avg latency (50 concurrent) | ~55s (rate-limited at 10 RPM) |

## License

MIT
