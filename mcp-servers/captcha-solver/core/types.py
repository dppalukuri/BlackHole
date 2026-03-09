"""Core data types for the CAPTCHA solver."""

from dataclasses import dataclass, field


# Challenge types
HCAPTCHA_GRID = "hcaptcha_grid"
HCAPTCHA_CANVAS_BUCKET = "hcaptcha_canvas_bucket"
HCAPTCHA_CANVAS_SILHOUETTE = "hcaptcha_canvas_silhouette"
HCAPTCHA_CANVAS_LINE = "hcaptcha_canvas_line"
HCAPTCHA_CANVAS_UNKNOWN = "hcaptcha_canvas_unknown"
RECAPTCHA_V2 = "recaptcha_v2"
RECAPTCHA_V3 = "recaptcha_v3"
TURNSTILE = "turnstile"
FUNCAPTCHA = "funcaptcha"


@dataclass
class CaptchaChallenge:
    """A CAPTCHA challenge to solve."""
    type: str                          # One of the constants above
    task_text: str = ""                # The instruction text
    images: list[str] = field(default_factory=list)  # Base64 data URIs or URLs
    is_canvas: bool = False            # Canvas-based challenge (single image)
    sitekey: str | None = None         # Site key for token-based solving
    page_url: str | None = None        # Page URL
    metadata: dict = field(default_factory=dict)


@dataclass
class SolveResult:
    """Result from a CAPTCHA solver."""
    success: bool
    solver_used: str = ""              # "clip_grid", "vlm", "token_api", etc.
    selections: list[int] = field(default_factory=list)  # Grid: matching image indices
    click_x: int | None = None         # Canvas: click X in canvas space
    click_y: int | None = None         # Canvas: click Y in canvas space
    canvas_width: int | None = None    # Canvas dimensions for scaling
    canvas_height: int | None = None
    token: str | None = None           # Token-based: CAPTCHA response token
    confidence: float = 0.0
    cost_usd: float = 0.0             # Estimated cost in USD
    solve_time_ms: int = 0
    error: str | None = None
    details: dict = field(default_factory=dict)


@dataclass
class SolverConfig:
    """Configuration for solver routing and behavior."""
    # VLM settings
    enable_vlm: bool = True
    vlm_provider: str = "gemini"       # "gemini" (free), "anthropic", "openai"
    vlm_api_key: str = ""
    vlm_model: str = ""                # Auto-selected per provider if empty

    # External API fallback
    enable_external_api: bool = False
    external_api_key: str = ""
    external_api_provider: str = "capsolver"  # "capsolver", "2captcha"

    # CLIP settings
    clip_threshold: float = 0.55
    vlm_confidence_gate: float = 0.45  # Below this, escalate CLIP → VLM

    # Cost control
    max_cost_per_solve: float = 0.01   # Budget cap per solve in USD
    prefer_local: bool = True          # Prefer free local solvers
