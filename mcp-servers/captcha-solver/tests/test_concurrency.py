"""
Concurrency stress test — 50 simultaneous CAPTCHA solves via Gemini VLM.

Tests:
  1. Can we handle 50 concurrent requests without crashes?
  2. How does Gemini rate limiting (10 RPM free tier) affect us?
  3. What's the success rate, latency distribution, and error breakdown?
  4. Memory/resource usage under load?

Run:
  set GEMINI_API_KEY=AIza...
  python tests/test_concurrency.py
"""

import os
import sys
import time
import asyncio
import base64
import tracemalloc
from io import BytesIO
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.types import SolverConfig
from router import CaptchaRouter


# ─── Synthetic test images ────────────────────────────────────────────

def make_test_image(color: tuple[int, int, int] = (200, 50, 50), size: int = 100) -> str:
    """Generate a small solid-color PNG as base64."""
    from PIL import Image
    img = Image.new("RGB", (size, size), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def make_grid_images(n: int = 9) -> list[str]:
    """Generate n different colored images simulating a CAPTCHA grid."""
    import random
    colors = [
        (200, 50, 50), (50, 200, 50), (50, 50, 200),
        (200, 200, 50), (200, 50, 200), (50, 200, 200),
        (150, 100, 50), (100, 150, 200), (200, 150, 100),
    ]
    return [make_test_image(colors[i % len(colors)]) for i in range(n)]


def make_canvas_image() -> str:
    """Generate a simple canvas-style image with shapes."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 400), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Draw some shapes to simulate a canvas challenge
    draw.ellipse([50, 50, 150, 150], fill=(255, 0, 0))       # red circle
    draw.rectangle([250, 250, 350, 350], fill=(0, 0, 255))    # blue square
    draw.ellipse([200, 50, 300, 150], fill=(0, 200, 0))       # green circle
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ─── Test harness ────────────────────────────────────────────────────

@dataclass
class SolveAttempt:
    id: int
    challenge_type: str  # "grid" or "canvas"
    success: bool = False
    solver_used: str = ""
    latency_ms: int = 0
    error: str = ""


async def solve_one(router: CaptchaRouter, attempt_id: int, challenge_type: str,
                    grid_images: list[str], canvas_image: str) -> SolveAttempt:
    """Run a single solve attempt."""
    attempt = SolveAttempt(id=attempt_id, challenge_type=challenge_type)
    t0 = time.time()

    try:
        if challenge_type == "grid":
            result = await router.solve_raw(
                task_text="Please click each image containing a red object",
                images=grid_images,
                is_canvas=False,
                captcha_type="hcaptcha",
            )
        else:
            result = await router.solve_raw(
                task_text="Click on the bucket that will catch the falling ball",
                images=[canvas_image],
                is_canvas=True,
                captcha_type="hcaptcha",
            )

        attempt.success = result.success
        attempt.solver_used = result.solver_used
        attempt.error = result.error or ""
    except Exception as e:
        attempt.error = f"{type(e).__name__}: {e}"

    attempt.latency_ms = int((time.time() - t0) * 1000)
    return attempt


async def run_concurrency_test(concurrency: int = 50, mix: str = "mixed"):
    """
    Fire `concurrency` simultaneous CAPTCHA solves.

    Args:
        concurrency: Number of simultaneous requests
        mix: "grid", "canvas", or "mixed" (50/50)
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY environment variable")
        return

    # Start memory tracking
    tracemalloc.start()
    mem_before = tracemalloc.get_traced_memory()[0]

    print(f"\n{'='*60}")
    print(f"  CAPTCHA Solver Concurrency Test")
    print(f"  Concurrency: {concurrency} simultaneous solves")
    print(f"  Challenge mix: {mix}")
    print(f"  VLM Provider: Gemini (free tier, 10 RPM limit)")
    print(f"{'='*60}\n")

    # Init router with Gemini
    config = SolverConfig(
        enable_vlm=True,
        vlm_provider="gemini",
        vlm_api_key=api_key,
        prefer_local=False,  # VLM first, skip CLIP download
        enable_external_api=False,
    )
    router = CaptchaRouter(config)

    # Generate test images once (reuse across requests)
    print("Generating test images...")
    grid_images = make_grid_images(9)
    canvas_image = make_canvas_image()
    print(f"  Grid: {len(grid_images)} images, ~{len(grid_images[0])//1000}KB each")
    print(f"  Canvas: 1 image, ~{len(canvas_image)//1000}KB")

    # Assign challenge types
    challenges = []
    for i in range(concurrency):
        if mix == "grid":
            ctype = "grid"
        elif mix == "canvas":
            ctype = "canvas"
        else:
            ctype = "grid" if i % 2 == 0 else "canvas"
        challenges.append(ctype)

    grid_count = sum(1 for c in challenges if c == "grid")
    canvas_count = concurrency - grid_count
    print(f"  Grid challenges: {grid_count}, Canvas challenges: {canvas_count}\n")

    # Fire all at once
    print(f"Launching {concurrency} concurrent solves...")
    t_start = time.time()

    tasks = [
        solve_one(router, i, ctype, grid_images, canvas_image)
        for i, ctype in enumerate(challenges)
    ]
    results: list[SolveAttempt] = await asyncio.gather(*tasks)

    t_total = time.time() - t_start
    mem_after = tracemalloc.get_traced_memory()[0]
    mem_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    # ─── Analyze results ─────────────────────────────────────────────

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    latencies = [r.latency_ms for r in results]

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Total time:        {t_total:.1f}s")
    print(f"  Throughput:        {concurrency / t_total:.1f} solves/sec")
    print(f"  Success rate:      {len(successes)}/{concurrency} ({100*len(successes)/concurrency:.0f}%)")
    print(f"  Failures:          {len(failures)}/{concurrency}")

    print(f"\n  Latency:")
    if latencies:
        latencies_sorted = sorted(latencies)
        print(f"    Min:             {latencies_sorted[0]}ms")
        print(f"    Median (p50):    {latencies_sorted[len(latencies_sorted)//2]}ms")
        print(f"    p90:             {latencies_sorted[int(len(latencies_sorted)*0.9)]}ms")
        print(f"    p99:             {latencies_sorted[int(len(latencies_sorted)*0.99)]}ms")
        print(f"    Max:             {latencies_sorted[-1]}ms")
        print(f"    Avg:             {sum(latencies)//len(latencies)}ms")

    print(f"\n  Memory:")
    print(f"    Before:          {mem_before / 1024 / 1024:.1f}MB")
    print(f"    After:           {mem_after / 1024 / 1024:.1f}MB")
    print(f"    Peak:            {mem_peak / 1024 / 1024:.1f}MB")

    # Breakdown by solver
    solvers_used = {}
    for r in results:
        key = r.solver_used or "none"
        solvers_used.setdefault(key, {"success": 0, "fail": 0})
        if r.success:
            solvers_used[key]["success"] += 1
        else:
            solvers_used[key]["fail"] += 1

    print(f"\n  Solver breakdown:")
    for solver, counts in solvers_used.items():
        total = counts["success"] + counts["fail"]
        print(f"    {solver:15s}  {counts['success']}/{total} succeeded")

    # Breakdown by challenge type
    for ctype in ("grid", "canvas"):
        subset = [r for r in results if r.challenge_type == ctype]
        if subset:
            ok = sum(1 for r in subset if r.success)
            lats = sorted([r.latency_ms for r in subset])
            print(f"\n  {ctype.upper()} challenges ({len(subset)} total):")
            print(f"    Success: {ok}/{len(subset)} ({100*ok/len(subset):.0f}%)")
            print(f"    Latency: {lats[0]}ms min, {lats[len(lats)//2]}ms median, {lats[-1]}ms max")

    # Error breakdown
    if failures:
        error_counts = {}
        for r in failures:
            err = r.error[:80] if r.error else "unknown"
            error_counts[err] = error_counts.get(err, 0) + 1

        print(f"\n  Error breakdown:")
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"    {count}x  {err}")

    # Per-request detail (first 10 + last 5)
    print(f"\n  Per-request detail (first 10):")
    print(f"  {'ID':>4s}  {'Type':>7s}  {'OK':>3s}  {'Solver':>12s}  {'Latency':>8s}  Error")
    print(f"  {'-'*4}  {'-'*7}  {'-'*3}  {'-'*12}  {'-'*8}  {'-'*20}")
    for r in results[:10]:
        ok = "YES" if r.success else "NO"
        print(f"  {r.id:4d}  {r.challenge_type:>7s}  {ok:>3s}  {r.solver_used:>12s}  {r.latency_ms:6d}ms  {r.error[:40]}")

    if len(results) > 15:
        print(f"  ... ({len(results) - 15} more) ...")
        for r in results[-5:]:
            ok = "YES" if r.success else "NO"
            print(f"  {r.id:4d}  {r.challenge_type:>7s}  {ok:>3s}  {r.solver_used:>12s}  {r.latency_ms:6d}ms  {r.error[:40]}")

    print(f"\n{'='*60}")
    print(f"  VERDICT")
    print(f"{'='*60}")

    success_pct = 100 * len(successes) / concurrency
    if success_pct >= 90:
        print(f"  PASS — {success_pct:.0f}% success rate at {concurrency} concurrency")
    elif success_pct >= 50:
        print(f"  PARTIAL — {success_pct:.0f}% success rate. Rate limiting likely.")
        print(f"  Need: request queuing, retry with backoff, or paid Gemini tier.")
    else:
        print(f"  FAIL — {success_pct:.0f}% success rate. Concurrency too high for free tier.")
        print(f"  Need: rate limiter, request queue, or higher API tier.")

    # Estimate what paid tier would cost
    if concurrency > 0:
        est_daily = concurrency * 10  # assume 10x daily volume
        est_monthly_cost = est_daily * 30 * 0.0001  # Gemini paid rate
        print(f"\n  At {est_daily} solves/day on Gemini paid: ~${est_monthly_cost:.2f}/month")

    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CAPTCHA solver concurrency test")
    parser.add_argument("-n", "--concurrency", type=int, default=50, help="Number of concurrent solves")
    parser.add_argument("--mix", choices=["grid", "canvas", "mixed"], default="mixed",
                        help="Challenge type mix")
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: Set GEMINI_API_KEY environment variable before running this test.")
        sys.exit(1)
    asyncio.run(run_concurrency_test(concurrency=args.concurrency, mix=args.mix))
