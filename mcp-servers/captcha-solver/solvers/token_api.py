"""External API solver — fallback to CapSolver/2Captcha."""

import time
import asyncio
import httpx
from core.types import CaptchaChallenge, SolveResult, SolverConfig
from solvers.base import BaseSolver

CAPSOLVER_API = "https://api.capsolver.com"
TWOCAPTCHA_API = "https://2captcha.com"


class ExternalAPISolver(BaseSolver):
    """Last-resort fallback: send CAPTCHA to external solving service."""

    name = "token_api"
    cost_per_solve = 0.002  # ~$2/1000 for most types

    async def can_solve(self, challenge: CaptchaChallenge) -> bool:
        return challenge.sitekey is not None and challenge.page_url is not None

    async def solve(self, challenge: CaptchaChallenge, config: SolverConfig) -> SolveResult:
        if not config.enable_external_api or not config.external_api_key:
            return SolveResult(success=False, solver_used=self.name,
                             error="External API not configured")

        t0 = time.time()

        if config.external_api_provider == "capsolver":
            token = await self._solve_capsolver(challenge, config.external_api_key)
        elif config.external_api_provider == "2captcha":
            token = await self._solve_2captcha(challenge, config.external_api_key)
        else:
            return SolveResult(success=False, solver_used=self.name,
                             error=f"Unknown API provider: {config.external_api_provider}")

        elapsed = int((time.time() - t0) * 1000)

        if token:
            return SolveResult(
                success=True, solver_used=self.name,
                token=token, confidence=0.9,
                cost_usd=self.cost_per_solve,
                solve_time_ms=elapsed,
            )
        return SolveResult(success=False, solver_used=self.name,
                         solve_time_ms=elapsed, error="External API failed")

    async def _solve_capsolver(self, challenge: CaptchaChallenge, api_key: str) -> str | None:
        type_map = {
            "hcaptcha_grid": "HCaptchaTaskProxyLess",
            "recaptcha_v2": "ReCaptchaV2TaskProxyLess",
            "recaptcha_v3": "ReCaptchaV3TaskProxyLess",
            "turnstile": "AntiTurnstileTaskProxyLess",
            "funcaptcha": "FunCaptchaTaskProxyLess",
        }
        # Normalize type (strip canvas subtypes to base)
        base_type = challenge.type.split("_canvas")[0] if "_canvas" in challenge.type else challenge.type
        task_type = type_map.get(base_type)
        if not task_type:
            return None

        async with httpx.AsyncClient(timeout=180) as client:
            task = {
                "type": task_type,
                "websiteURL": challenge.page_url,
                "websiteKey": challenge.sitekey,
            }
            # reCAPTCHA v3 requires action and minimum score
            if challenge.type == "recaptcha_v3":
                task["pageAction"] = challenge.metadata.get("action", "verify")
                task["minScore"] = challenge.metadata.get("min_score", 0.7)

            resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
                "clientKey": api_key,
                "task": task,
            })
            data = resp.json()
            if data.get("errorId", 0) != 0:
                return None

            task_id = data.get("taskId")
            if not task_id:
                return None

            for _ in range(40):
                await asyncio.sleep(3)
                resp = await client.post(f"{CAPSOLVER_API}/getTaskResult", json={
                    "clientKey": api_key, "taskId": task_id,
                })
                result = resp.json()
                if result.get("status") == "ready":
                    solution = result.get("solution", {})
                    return solution.get("gRecaptchaResponse") or solution.get("token")
                elif result.get("status") == "failed":
                    return None

        return None

    async def _solve_2captcha(self, challenge: CaptchaChallenge, api_key: str) -> str | None:
        type_map = {
            "hcaptcha_grid": "hcaptcha",
            "recaptcha_v2": "userrecaptcha",
            "recaptcha_v3": "userrecaptcha",
            "turnstile": "turnstile",
        }
        base_type = challenge.type.split("_canvas")[0] if "_canvas" in challenge.type else challenge.type
        method = type_map.get(base_type)
        if not method:
            return None

        async with httpx.AsyncClient(timeout=180) as client:
            params = {
                "key": api_key,
                "method": method,
                "sitekey": challenge.sitekey,
                "pageurl": challenge.page_url,
                "json": 1,
            }
            # reCAPTCHA v3 requires version, action, and min_score
            if challenge.type == "recaptcha_v3":
                params["version"] = "v3"
                params["action"] = challenge.metadata.get("action", "verify")
                params["min_score"] = challenge.metadata.get("min_score", 0.7)
            resp = await client.get(f"{TWOCAPTCHA_API}/in.php", params=params)
            data = resp.json()
            if data.get("status") != 1:
                return None

            task_id = data.get("request")

            for _ in range(40):
                await asyncio.sleep(5)
                resp = await client.get(f"{TWOCAPTCHA_API}/res.php", params={
                    "key": api_key, "action": "get", "id": task_id, "json": 1,
                })
                result = resp.json()
                if result.get("status") == 1:
                    return result.get("request")
                elif "ERROR" in str(result.get("request", "")):
                    return None

        return None
