"""CLIP-based solver for hCaptcha canvas challenges (silhouette, line, bucket)."""

import asyncio
import re
import base64
import io
import numpy as np
from PIL import Image

from core.types import (
    CaptchaChallenge, SolveResult, SolverConfig,
    HCAPTCHA_CANVAS_BUCKET, HCAPTCHA_CANVAS_SILHOUETTE,
    HCAPTCHA_CANVAS_LINE, HCAPTCHA_CANVAS_UNKNOWN,
)
from solvers.base import BaseSolver

CANVAS_TYPES = {HCAPTCHA_CANVAS_BUCKET, HCAPTCHA_CANVAS_SILHOUETTE,
                HCAPTCHA_CANVAS_LINE, HCAPTCHA_CANVAS_UNKNOWN}


def _decode_canvas(data_url: str):
    """Decode canvas data URL to numpy array and find content bounds."""
    b64_data = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_data)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]

    alpha = arr[:, :, 3]
    content_rows = np.where(np.any(alpha > 10, axis=1))[0]
    content_cols = np.where(np.any(alpha > 10, axis=0))[0]

    if len(content_rows) == 0:
        return None

    y_start = int(content_rows.min())
    y_end = int(content_rows.max())
    x_start = int(content_cols.min())
    x_end = int(content_cols.max())
    content = arr[y_start:y_end + 1, x_start:x_end + 1]

    return {
        "arr": arr, "content": content,
        "w": w, "h": h,
        "x_start": x_start, "y_start": y_start,
    }


def _solve_bucket(data_url: str) -> dict | None:
    """Solve bucket/ball challenge using connected component analysis."""
    from scipy.ndimage import label as scipy_label

    parsed = _decode_canvas(data_url)
    if not parsed:
        return None

    content = parsed["content"]
    ch, cw = content.shape[:2]
    x_start, y_start = parsed["x_start"], parsed["y_start"]
    w, h = parsed["w"], parsed["h"]

    # Find red ball
    rgb = content[:, :, :3].astype(float)
    red_mask = (rgb[:, :, 0] > 150) & (rgb[:, :, 1] < 100) & (rgb[:, :, 2] < 100)
    red_mask[ch // 2:, :] = False

    if not red_mask.any():
        return None

    ys, xs = np.where(red_mask)
    ball_x = int(xs.mean())
    ball_y = int(ys.max())

    # Adaptive threshold for pipe detection
    alpha = content[:, :, 3]
    gray = np.mean(content[:, :, :3], axis=2)
    visible_mask = alpha > 10
    if not visible_mask.any():
        return None

    visible_gray = gray[visible_mask]
    p25 = float(np.percentile(visible_gray, 25))
    p75 = float(np.percentile(visible_gray, 75))
    median_bright = float(np.median(visible_gray))

    if p75 - p25 > 20:
        threshold = (median_bright + p75) / 2
    else:
        threshold = median_bright + 15

    pipe_mask = visible_mask & (gray > threshold) & ~red_mask

    # Connected component analysis
    labeled, n_components = scipy_label(pipe_mask)

    # Find component near ball
    search_y0 = max(0, ball_y - 5)
    search_y1 = min(ch, ball_y + 25)
    search_x0 = max(0, ball_x - 20)
    search_x1 = min(cw, ball_x + 20)
    region_labels = labeled[search_y0:search_y1, search_x0:search_x1]
    unique_labels = np.unique(region_labels)
    unique_labels = unique_labels[unique_labels > 0]

    if len(unique_labels) == 0:
        # Widen search
        search_y1 = min(ch, ball_y + 60)
        search_x0 = max(0, ball_x - 50)
        search_x1 = min(cw, ball_x + 50)
        region_labels = labeled[search_y0:search_y1, search_x0:search_x1]
        unique_labels = np.unique(region_labels)
        unique_labels = unique_labels[unique_labels > 0]

    if len(unique_labels) == 0:
        return {"x": x_start + ball_x, "y": y_start + int(ch * 0.88),
                "w": w, "h": h, "confidence": 0.2}

    best_label = max(unique_labels, key=lambda lbl: np.count_nonzero(labeled == lbl))
    component_mask = labeled == best_label
    comp_ys, comp_xs = np.where(component_mask)

    y_threshold = int(comp_ys.max() - (comp_ys.max() - comp_ys.min()) * 0.15)
    bottom_mask = comp_ys >= y_threshold
    bucket_x = int(np.median(comp_xs[bottom_mask])) if bottom_mask.any() else int(comp_xs.mean())

    return {"x": x_start + bucket_x, "y": y_start + int(ch * 0.88),
            "w": w, "h": h, "confidence": 0.6}


def _solve_silhouette(data_url: str) -> dict | None:
    """Solve silhouette matching using CLIP image-to-image embedding similarity."""
    from vision.clip import get_image_embeddings

    parsed = _decode_canvas(data_url)
    if not parsed:
        return None

    content = parsed["content"]
    ch, cw = content.shape[:2]
    x_start, y_start = parsed["x_start"], parsed["y_start"]
    w, h = parsed["w"], parsed["h"]

    rows, cols = 3, 3
    cell_h = ch // rows
    cell_w = cw // cols

    cells = []
    cell_images = []
    for r in range(rows):
        for c in range(cols):
            y1 = r * cell_h
            y2 = (r + 1) * cell_h
            x1 = c * cell_w
            x2 = (c + 1) * cell_w
            cell = content[y1:y2, x1:x2]

            cx = x_start + x1 + cell_w // 2
            cy = y_start + y1 + cell_h // 2

            cell_alpha = cell[:, :, 3]
            content_ratio = float(np.count_nonzero(cell_alpha > 10)) / cell_alpha.size

            if content_ratio > 0.02:
                mask = cell_alpha > 10
                cell_rgb = cell[:, :, :3].astype(float)
                saturation = float(np.std(cell_rgb[mask], axis=1).mean()) if mask.any() else 0.0
            else:
                saturation = 0.0

            cells.append({"center_x": cx, "center_y": cy,
                         "content_ratio": content_ratio, "saturation": saturation})
            cell_images.append(Image.fromarray(cell).convert("RGB"))

    active = [i for i, c in enumerate(cells) if c["content_ratio"] > 0.02]
    if not active:
        return None

    ref_idx = max(active, key=lambda i: cells[i]["saturation"])

    embeddings = np.array(get_image_embeddings(cell_images))
    ref_emb = embeddings[ref_idx]
    similarities = embeddings @ ref_emb

    candidates = [(i, float(similarities[i])) for i in active if i != ref_idx]
    if not candidates:
        return None

    best_idx, best_sim = max(candidates, key=lambda x: x[1])
    target = cells[best_idx]

    return {"x": target["center_x"], "y": target["center_y"],
            "w": w, "h": h, "confidence": best_sim}


def _solve_line(data_url: str, shape_name: str) -> dict | None:
    """Solve line-connection challenge using CLIP text classification."""
    from vision.clip import classify_image

    parsed = _decode_canvas(data_url)
    if not parsed:
        return None

    content = parsed["content"]
    ch, cw = content.shape[:2]
    x_start, y_start = parsed["x_start"], parsed["y_start"]
    w, h = parsed["w"], parsed["h"]

    labels = [
        f"a {shape_name} connected by a solid straight line",
        f"a {shape_name} connected by a dashed or dotted line",
        "a colorful psychedelic background pattern",
        "a center point with radiating lines",
    ]

    grid = 4
    cell_h = ch // grid
    cell_w = cw // grid

    candidates = []
    for r in range(grid):
        for c in range(grid):
            y1 = r * cell_h
            y2 = (r + 1) * cell_h
            x1 = c * cell_w
            x2 = (c + 1) * cell_w
            cell = content[y1:y2, x1:x2]
            cell_rgb = cell[:, :, :3].astype(float)
            brightness = float(np.mean(cell_rgb))

            candidates.append({
                "canvas_x": x_start + x1 + cell_w // 2,
                "canvas_y": y_start + y1 + cell_h // 2,
                "brightness": brightness,
                "image": Image.fromarray(cell).convert("RGB"),
            })

    candidates.sort(key=lambda c: -c["brightness"])

    best_score = -1
    best_result = None
    for cand in candidates[:8]:
        results = classify_image(cand["image"], labels)
        solid_score = results.get(labels[0], 0)

        if solid_score > best_score:
            best_score = solid_score
            best_result = {"x": cand["canvas_x"], "y": cand["canvas_y"],
                          "w": w, "h": h, "confidence": solid_score}

    return best_result


class CLIPCanvasSolver(BaseSolver):
    """Solve hCaptcha canvas challenges using CLIP (bucket, silhouette, line)."""

    name = "clip_canvas"
    cost_per_solve = 0.0

    async def can_solve(self, challenge: CaptchaChallenge) -> bool:
        return challenge.type in CANVAS_TYPES and challenge.is_canvas and len(challenge.images) == 1

    async def solve(self, challenge: CaptchaChallenge, config: SolverConfig) -> SolveResult:
        import time
        t0 = time.time()

        data_url = challenge.images[0]
        task_lower = challenge.task_text.lower()

        if challenge.type == HCAPTCHA_CANVAS_BUCKET:
            result = await asyncio.to_thread(_solve_bucket, data_url)
        elif challenge.type == HCAPTCHA_CANVAS_LINE:
            shape_match = re.search(r'outer\s+(\w+)', challenge.task_text, re.I)
            shape_name = shape_match.group(1).lower() if shape_match else "shape"
            result = await asyncio.to_thread(_solve_line, data_url, shape_name)
        elif challenge.type == HCAPTCHA_CANVAS_SILHOUETTE:
            result = await asyncio.to_thread(_solve_silhouette, data_url)
        else:
            # Unknown canvas type — try auto-detection
            result = await asyncio.to_thread(_solve_bucket, data_url)
            if not result:
                result = await asyncio.to_thread(_solve_silhouette, data_url)

        if not result:
            return SolveResult(success=False, solver_used=self.name, error="No solution found")

        return SolveResult(
            success=True,
            solver_used=self.name,
            click_x=result["x"],
            click_y=result["y"],
            canvas_width=result["w"],
            canvas_height=result["h"],
            confidence=result["confidence"],
            solve_time_ms=int((time.time() - t0) * 1000),
        )
