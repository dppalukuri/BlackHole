"""
REST API for CAPTCHA Solver — 2Captcha/CapSolver compatible.

Drop-in replacement for existing CAPTCHA solving services.
Supports both CapSolver format (/createTask) and direct format (/solve).

Run:
  uvicorn api:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import uuid
import asyncio
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.types import CaptchaChallenge, SolverConfig
from router import CaptchaRouter, classify_challenge

app = FastAPI(title="CAPTCHA Solver API", version="2.0.0")

# In-memory task store (upgrade to Redis for production)
_tasks: dict[str, dict] = {}
_router: CaptchaRouter | None = None


def _get_router() -> CaptchaRouter:
    global _router
    if _router is None:
        from server import _load_config
        _router = CaptchaRouter(_load_config())
    return _router


# ─── Direct API ───────────────────────────────────────────────────────

class SolveRequest(BaseModel):
    task_text: str
    images: list[str]
    captcha_type: str = "hcaptcha"
    is_canvas: bool = False
    sitekey: str | None = None
    page_url: str | None = None


class SolveResponse(BaseModel):
    success: bool
    solver: str = ""
    selections: list[int] | None = None
    click_x: int | None = None
    click_y: int | None = None
    canvas_width: int | None = None
    canvas_height: int | None = None
    token: str | None = None
    confidence: float = 0.0
    cost_usd: float = 0.0
    solve_time_ms: int = 0
    error: str | None = None


@app.post("/solve", response_model=SolveResponse)
async def solve_direct(req: SolveRequest):
    """Solve a CAPTCHA directly. Returns result immediately."""
    router = _get_router()
    result = await router.solve_raw(
        task_text=req.task_text,
        images=req.images,
        is_canvas=req.is_canvas,
        captcha_type=req.captcha_type,
        sitekey=req.sitekey,
        page_url=req.page_url,
    )
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


# ─── CapSolver-compatible API ─────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    clientKey: str = ""
    task: dict[str, Any] = {}


class CreateTaskResponse(BaseModel):
    errorId: int = 0
    errorDescription: str = ""
    taskId: str = ""


class GetTaskResultRequest(BaseModel):
    clientKey: str = ""
    taskId: str = ""


class GetTaskResultResponse(BaseModel):
    errorId: int = 0
    status: str = "processing"  # "processing" or "ready"
    solution: dict[str, Any] = {}


@app.post("/createTask", response_model=CreateTaskResponse)
async def create_task(req: CreateTaskRequest):
    """CapSolver-compatible task creation."""
    task = req.task
    task_type = task.get("type", "")
    website_url = task.get("websiteURL", "")
    website_key = task.get("websiteKey", "")

    # Map CapSolver task types to our types
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
    }

    # Start solving in background
    asyncio.create_task(_solve_task(task_id, captcha_type, website_url, website_key))

    return CreateTaskResponse(taskId=task_id)


@app.post("/getTaskResult", response_model=GetTaskResultResponse)
async def get_task_result(req: GetTaskResultRequest):
    """CapSolver-compatible task result polling."""
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
    except Exception:
        _tasks[task_id] = {"status": "failed"}


# ─── Health ───────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/status")
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
