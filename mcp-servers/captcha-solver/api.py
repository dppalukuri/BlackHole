"""
REST API for CAPTCHA Solver -- 2Captcha/CapSolver compatible.

Drop-in replacement for existing CAPTCHA solving services.
Supports both CapSolver format (/createTask) and direct format (/solve).

Auth modes:
  - Direct: Bearer token (API_KEYS env var)
  - RapidAPI: X-RapidAPI-Proxy-Secret header
  - CapSolver compat: clientKey in JSON body

Run:
  uvicorn api:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import uuid
import asyncio
import hashlib
import logging
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from core.types import CaptchaChallenge, SolverConfig
from router import CaptchaRouter, classify_challenge

logger = logging.getLogger("captcha_solver.api")

app = FastAPI(
    title="CAPTCHA Solver API",
    version="2.0.0",
    description=(
        "AI-powered CAPTCHA solver with free tier. Uses CLIP (local) and Gemini Vision (free) "
        "to solve hCaptcha, reCAPTCHA, Turnstile, and FunCaptcha challenges. "
        "Drop-in compatible with 2Captcha and CapSolver APIs."
    ),
)

# ---- Auth ----------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)

# API keys: loaded from API_KEYS env var (comma-separated) or API_KEYS_FILE
_valid_keys: set[str] = set()

# RapidAPI proxy secret: if set, requests with matching X-RapidAPI-Proxy-Secret
# header are authenticated (RapidAPI handles user billing/rate limiting)
_rapidapi_secret: str = ""


def _load_api_keys():
    """Load valid API keys from environment."""
    global _valid_keys, _rapidapi_secret
    keys_raw = os.environ.get("API_KEYS", "")
    if keys_raw:
        _valid_keys = {k.strip() for k in keys_raw.split(",") if k.strip()}

    keys_file = os.environ.get("API_KEYS_FILE", "")
    if keys_file and os.path.isfile(keys_file):
        with open(keys_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    _valid_keys.add(line)

    _rapidapi_secret = os.environ.get("RAPIDAPI_PROXY_SECRET", "")

    if not _valid_keys and not _rapidapi_secret:
        logger.warning("No API_KEYS or RAPIDAPI_PROXY_SECRET configured. "
                       "Set at least one for authentication.")


def _hash_key(key: str) -> str:
    """Hash a key for safe logging."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Validate API key from Bearer token, RapidAPI proxy, or clientKey field."""
    # 1. RapidAPI proxy secret (highest priority -- RapidAPI handles user auth)
    rapidapi_header = request.headers.get("x-rapidapi-proxy-secret", "")
    if _rapidapi_secret and rapidapi_header == _rapidapi_secret:
        # Use RapidAPI subscriber info for logging
        subscriber = request.headers.get("x-rapidapi-user", "rapidapi-user")
        return f"rapidapi:{subscriber}"

    # 2. Bearer token
    if credentials and credentials.credentials in _valid_keys:
        return credentials.credentials

    # 3. CapSolver compat: clientKey in JSON body
    if request.method == "POST":
        try:
            body = await request.json()
            client_key = body.get("clientKey", "")
            if client_key and client_key in _valid_keys:
                return client_key
        except Exception:
            pass

    raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---- Rate limiting -------------------------------------------------------

# Simple in-memory rate limiter per API key
_rate_log: dict[str, list[float]] = {}

RATE_LIMIT_RPM = int(os.environ.get("RATE_LIMIT_RPM", "30"))


def _check_rate_limit(api_key: str):
    """Raise 429 if key exceeds rate limit. Skipped for RapidAPI (they enforce their own)."""
    if api_key.startswith("rapidapi:"):
        return  # RapidAPI proxy handles rate limiting

    key_hash = _hash_key(api_key)
    now = time.time()
    window_start = now - 60

    if key_hash not in _rate_log:
        _rate_log[key_hash] = []

    _rate_log[key_hash] = [t for t in _rate_log[key_hash] if t > window_start]

    if len(_rate_log[key_hash]) >= RATE_LIMIT_RPM:
        logger.warning("Rate limit hit for key %s (%d RPM)", key_hash, RATE_LIMIT_RPM)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT_RPM} requests per minute. Try again shortly.",
        )

    _rate_log[key_hash].append(now)


# ---- Router singleton ----------------------------------------------------

_tasks: dict[str, dict] = {}
_router: CaptchaRouter | None = None


def _get_router() -> CaptchaRouter:
    global _router
    if _router is None:
        from server import _load_config
        _router = CaptchaRouter(_load_config())
    return _router


# ---- Startup -------------------------------------------------------------

@app.on_event("startup")
async def startup():
    _load_api_keys()
    logger.info("CAPTCHA Solver API started. keys=%d rapidapi=%s",
                len(_valid_keys), bool(_rapidapi_secret))


# ---- Direct API ----------------------------------------------------------

class SolveRequest(BaseModel):
    task_text: str = Field(..., description="The CAPTCHA challenge instruction text (e.g. 'Click each image containing a bus')")
    images: list[str] = Field(..., description="List of images as base64 data URIs or URLs")
    captcha_type: str = Field("hcaptcha", description="Type: hcaptcha, recaptcha, recaptcha_v3, turnstile, funcaptcha")
    is_canvas: bool = Field(False, description="True if this is a single canvas/interactive challenge (not a grid)")
    sitekey: str | None = Field(None, description="Site key for token-based solving (reCAPTCHA v3, Turnstile)")
    page_url: str | None = Field(None, description="Page URL for token-based solving")


class SolveResponse(BaseModel):
    success: bool = Field(..., description="Whether the CAPTCHA was solved successfully")
    solver: str = Field("", description="Which solver was used: clip_grid, vlm, token_api")
    selections: list[int] | None = Field(None, description="Grid challenges: indices of matching images (0-indexed)")
    click_x: int | None = Field(None, description="Canvas challenges: X coordinate to click")
    click_y: int | None = Field(None, description="Canvas challenges: Y coordinate to click")
    canvas_width: int | None = Field(None, description="Canvas width for coordinate scaling")
    canvas_height: int | None = Field(None, description="Canvas height for coordinate scaling")
    token: str | None = Field(None, description="Token-based challenges: CAPTCHA response token")
    confidence: float = Field(0.0, description="Solver confidence score (0.0 to 1.0)")
    cost_usd: float = Field(0.0, description="Estimated cost of this solve in USD")
    solve_time_ms: int = Field(0, description="Time taken to solve in milliseconds")
    error: str | None = Field(None, description="Error message if solving failed")


@app.post("/solve", response_model=SolveResponse, summary="Solve a CAPTCHA",
          description="Submit a CAPTCHA challenge and get the solution immediately. "
                      "Supports image grids (hCaptcha, reCAPTCHA v2), canvas challenges "
                      "(hCaptcha interactive), and token-based challenges (reCAPTCHA v3, Turnstile).")
async def solve_direct(req: SolveRequest, api_key: str = Depends(require_auth)):
    _check_rate_limit(api_key)
    router = _get_router()
    t0 = time.time()
    result = await router.solve_raw(
        task_text=req.task_text,
        images=req.images,
        is_canvas=req.is_canvas,
        captcha_type=req.captcha_type,
        sitekey=req.sitekey,
        page_url=req.page_url,
    )
    logger.info("solve key=%s type=%s solver=%s success=%s time=%dms",
                _hash_key(api_key), req.captcha_type, result.solver_used,
                result.success, int((time.time() - t0) * 1000))
    return SolveResponse(
        success=result.success,
        solver=result.solver_used,
        selections=result.selections or None,
        click_x=result.click_x,
        click_y=result.click_y,
        canvas_width=result.canvas_width,
        canvas_height=result.canvas_height,
        token=result.token,
        confidence=round(result.confidence, 4),
        cost_usd=round(result.cost_usd, 6),
        solve_time_ms=result.solve_time_ms,
        error=result.error,
    )


# ---- CapSolver-compatible API --------------------------------------------

class CreateTaskRequest(BaseModel):
    clientKey: str = Field("", description="Your API key (CapSolver compatibility)")
    task: dict[str, Any] = Field({}, description="Task object with type, websiteURL, websiteKey")


class CreateTaskResponse(BaseModel):
    errorId: int = Field(0, description="0 = success, 1 = error")
    errorDescription: str = Field("", description="Error description if errorId > 0")
    taskId: str = Field("", description="Task ID for polling with /getTaskResult")


class GetTaskResultRequest(BaseModel):
    clientKey: str = Field("", description="Your API key")
    taskId: str = Field("", description="Task ID from /createTask response")


class GetTaskResultResponse(BaseModel):
    errorId: int = Field(0, description="0 = success, 1 = error")
    status: str = Field("processing", description="'processing' or 'ready'")
    solution: dict[str, Any] = Field({}, description="Solution object when status is 'ready'")


@app.post("/createTask", response_model=CreateTaskResponse,
          summary="Create a CAPTCHA task (CapSolver compatible)",
          description="Create an async CAPTCHA solving task. Compatible with CapSolver API format. "
                      "Supported types: HCaptchaTaskProxyLess, ReCaptchaV2TaskProxyLess, "
                      "ReCaptchaV3TaskProxyLess, AntiTurnstileTaskProxyLess, FunCaptchaTaskProxyLess.")
async def create_task(req: CreateTaskRequest, api_key: str = Depends(require_auth)):
    _check_rate_limit(api_key)
    task = req.task
    task_type = task.get("type", "")
    website_url = task.get("websiteURL", "")
    website_key = task.get("websiteKey", "")

    type_map = {
        "HCaptchaTaskProxyLess": "hcaptcha",
        "HCaptchaTask": "hcaptcha",
        "ReCaptchaV2TaskProxyLess": "recaptcha",
        "ReCaptchaV2Task": "recaptcha",
        "ReCaptchaV3TaskProxyLess": "recaptcha_v3",
        "AntiTurnstileTaskProxyLess": "turnstile",
        "FunCaptchaTaskProxyLess": "funcaptcha",
    }

    captcha_type = type_map.get(task_type)
    if not captcha_type:
        return CreateTaskResponse(errorId=1, errorDescription=f"Unknown task type: {task_type}")

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "processing",
        "captcha_type": captcha_type,
        "website_url": website_url,
        "website_key": website_key,
        "created_at": time.time(),
        "owner": _hash_key(api_key),
    }

    asyncio.create_task(_solve_task(task_id, captcha_type, website_url, website_key))
    logger.info("createTask key=%s type=%s task_id=%s", _hash_key(api_key), captcha_type, task_id)

    return CreateTaskResponse(taskId=task_id)


@app.post("/getTaskResult", response_model=GetTaskResultResponse,
          summary="Get task result (CapSolver compatible)",
          description="Poll for the result of an async CAPTCHA task created with /createTask.")
async def get_task_result(req: GetTaskResultRequest, api_key: str = Depends(require_auth)):
    task = _tasks.get(req.taskId)
    if not task:
        return GetTaskResultResponse(errorId=1)

    if task["status"] == "ready":
        return GetTaskResultResponse(status="ready", solution=task.get("solution", {}))
    elif task["status"] == "failed":
        return GetTaskResultResponse(errorId=1)

    return GetTaskResultResponse(status="processing")


async def _solve_task(task_id: str, captcha_type: str, website_url: str, website_key: str):
    """Background task to solve a CAPTCHA."""
    try:
        router = _get_router()
        challenge = CaptchaChallenge(
            type=classify_challenge("", [], False, captcha_type),
            sitekey=website_key,
            page_url=website_url,
        )
        result = await router.solve(challenge)

        if result.success and result.token:
            _tasks[task_id] = {
                "status": "ready",
                "solution": {
                    "gRecaptchaResponse": result.token,
                    "token": result.token,
                },
            }
        else:
            _tasks[task_id] = {"status": "failed"}
    except Exception as e:
        logger.error("Task %s failed: %s", task_id, e)
        _tasks[task_id] = {"status": "failed"}


# ---- Health (no auth required) -------------------------------------------

@app.get("/health", summary="Health check",
         description="Returns API status. No authentication required.")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/status", summary="Solver status",
         description="Returns which solvers are available and active task count. No authentication required.")
async def status():
    router = _get_router()
    config = router.config
    return {
        "solvers": {
            "clip": True,
            "vlm": config.enable_vlm,
            "external_api": config.enable_external_api,
        },
        "active_tasks": len([t for t in _tasks.values() if t.get("status") == "processing"]),
    }
