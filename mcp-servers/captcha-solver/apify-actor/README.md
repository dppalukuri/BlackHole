# AI CAPTCHA Solver

Solve CAPTCHAs using AI vision models. **Free tier included** -- no paid API key required for basic solving.

Uses CLIP (free, local) and Google Gemini Vision (free, 250/day) to solve image-based CAPTCHAs. Drop-in compatible with existing CAPTCHA solving workflows.

## Supported CAPTCHA Types

| Type | Method | Cost |
|------|--------|------|
| hCaptcha image grids | CLIP / Gemini VLM | Free |
| hCaptcha canvas (bucket, silhouette, line) | Gemini VLM | Free |
| reCAPTCHA v2 image selection | CLIP / Gemini VLM | Free |
| FunCaptcha | Gemini VLM | Free |

## How It Works

1. Submit CAPTCHA images + challenge text
2. AI analyzes the images and identifies the solution
3. Returns matched image indices (grids) or click coordinates (canvas)

Smart routing: tries the cheapest solver first, escalates on failure.

```
CLIP (free, local) --> Gemini Vision (free, 250/day) --> fallback
```

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `taskText` | string | Yes* | Challenge instruction (e.g. "Click each image containing a bus") |
| `images` | array | Yes* | Image URLs or base64 data URIs |
| `captchaType` | string | No | hcaptcha (default), recaptcha, funcaptcha |
| `isCanvas` | boolean | No | True for canvas/interactive challenges |
| `geminiApiKey` | string | No | Gemini API key for VLM solving (free at aistudio.google.com) |

*Either `images` + `taskText` (visual) or `sitekey` + `pageUrl` (token-based) required.

## Output

```json
{
    "success": true,
    "solver": "vlm",
    "selections": [0, 3, 7],
    "confidence": 0.75,
    "solveTimeMs": 3200
}
```

For canvas challenges:
```json
{
    "success": true,
    "solver": "vlm",
    "clickX": 234,
    "clickY": 156,
    "canvasWidth": 1000,
    "canvasHeight": 940,
    "confidence": 0.70
}
```

## Pricing

**$0.003 per successful solve** (you only pay when the CAPTCHA is solved).

- 100 solves = $0.30
- 1,000 solves = $3.00
- 10,000 solves = $30.00

Compare: 2Captcha charges $2.70-3.50/1000, CapSolver charges $0.80-1.00/1000.

## Tips

- Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) for best results
- For image grids, provide all cell images individually (not the whole grid as one image)
- Canvas challenges return pixel coordinates -- scale to your actual canvas size using canvasWidth/canvasHeight
