"""Vision Language Model client for CAPTCHA solving.

Supports Google Gemini (free), Anthropic (Claude), and OpenAI (GPT-4o).
The VLM can solve challenges that CLIP cannot: complex spatial reasoning,
3D puzzles, novel challenge types, etc.
"""

import json
import re
import base64


# Default models per provider
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o-mini",
}

# Cost estimates per image (USD)
COST_ESTIMATES = {
    "gemini": 0.0,       # Free tier: 10 RPM, 250 RPD
    "anthropic": 0.004,
    "openai": 0.002,
}


def _extract_json(text: str) -> dict | None:
    """Extract JSON object from VLM response text."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


async def solve_canvas_vlm(
    canvas_b64: str,
    task_text: str,
    provider: str = "anthropic",
    api_key: str = "",
    model: str = "",
) -> dict | None:
    """
    Ask a VLM to solve a canvas CAPTCHA challenge.

    Args:
        canvas_b64: Base64-encoded PNG image (with or without data: prefix)
        task_text: The challenge instruction
        provider: "anthropic" or "openai"
        api_key: API key for the provider
        model: Model name (auto-selected if empty)

    Returns:
        {"x": int, "y": int, "reasoning": str, "confidence": float} or None
    """
    if not api_key:
        return None

    # Clean base64
    if "," in canvas_b64:
        canvas_b64 = canvas_b64.split(",", 1)[1]

    model = model or DEFAULT_MODELS.get(provider, "")

    prompt = (
        f"This is a CAPTCHA challenge image. The task says: \"{task_text}\"\n\n"
        "Analyze the image carefully and determine the exact pixel coordinates "
        "where I should click to solve this challenge.\n\n"
        "Rules:\n"
        "- If it says 'bucket that will catch the ball', trace the pipe path from the red ball to the correct bucket\n"
        "- If it says 'silhouette', find the silhouette matching the colored character in the center\n"
        "- If it says 'solid line', find the outer shape connected by a solid (not dashed) line\n"
        "- Return coordinates relative to the image (0,0 is top-left)\n\n"
        "Return ONLY a JSON object: {\"x\": 123, \"y\": 456, \"reasoning\": \"brief explanation\"}"
    )

    if provider == "gemini":
        return await _solve_gemini(canvas_b64, prompt, api_key, model)
    elif provider == "anthropic":
        return await _solve_anthropic(canvas_b64, prompt, api_key, model)
    elif provider == "openai":
        return await _solve_openai(canvas_b64, prompt, api_key, model)
    return None


async def solve_grid_vlm(
    images_b64: list[str],
    task_text: str,
    provider: str = "anthropic",
    api_key: str = "",
    model: str = "",
) -> dict | None:
    """
    Ask a VLM to solve an image grid CAPTCHA.

    Returns:
        {"selections": [0, 3, 7], "reasoning": str} or None
    """
    if not api_key:
        return None

    model = model or DEFAULT_MODELS.get(provider, "")
    n = len(images_b64)

    prompt = (
        f"This is a CAPTCHA with {n} images arranged in a grid. "
        f"The task says: \"{task_text}\"\n\n"
        f"Which images match the task? Images are numbered 0 to {n-1}, "
        "left to right, top to bottom.\n\n"
        "Return ONLY a JSON object: {\"selections\": [0, 3, 7], \"reasoning\": \"brief explanation\"}"
    )

    if provider == "gemini":
        return await _solve_grid_gemini(images_b64, prompt, api_key, model)
    elif provider == "anthropic":
        return await _solve_grid_anthropic(images_b64, prompt, api_key, model)
    elif provider == "openai":
        return await _solve_grid_openai(images_b64, prompt, api_key, model)
    return None


async def _solve_anthropic(image_b64: str, prompt: str, api_key: str, model: str) -> dict | None:
    """Solve using Anthropic Claude Vision."""
    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        message = await client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        }
                    },
                    {"type": "text", "text": prompt},
                ]
            }]
        )
        text = message.content[0].text
        return _extract_json(text)
    except Exception:
        return None


async def _solve_openai(image_b64: str, prompt: str, api_key: str, model: str) -> dict | None:
    """Solve using OpenAI GPT-4o Vision."""
    try:
        import openai
    except ImportError:
        return None

    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    },
                    {"type": "text", "text": prompt},
                ]
            }]
        )
        text = response.choices[0].message.content
        return _extract_json(text)
    except Exception:
        return None


async def _solve_grid_anthropic(images_b64: list[str], prompt: str, api_key: str, model: str) -> dict | None:
    """Solve grid challenge using Anthropic Claude Vision."""
    try:
        import anthropic
    except ImportError:
        return None

    # Build content with all images + prompt
    content = []
    for i, img_b64 in enumerate(images_b64):
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
        })
        content.append({"type": "text", "text": f"(Image {i})"})
    content.append({"type": "text", "text": prompt})

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        message = await client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": content}]
        )
        text = message.content[0].text
        return _extract_json(text)
    except Exception:
        return None


async def _solve_grid_openai(images_b64: list[str], prompt: str, api_key: str, model: str) -> dict | None:
    """Solve grid challenge using OpenAI GPT-4o Vision."""
    try:
        import openai
    except ImportError:
        return None

    content = []
    for i, img_b64 in enumerate(images_b64):
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })
        content.append({"type": "text", "text": f"(Image {i})"})
    content.append({"type": "text", "text": prompt})

    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": content}]
        )
        text = response.choices[0].message.content
        return _extract_json(text)
    except Exception:
        return None


# ─── Google Gemini (FREE) ────────────────────────────────────────────


def _b64_to_gemini_part(img_b64: str):
    """Convert base64 image to Gemini Part object."""
    from google.genai import types
    if "," in img_b64:
        img_b64 = img_b64.split(",", 1)[1]
    return types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type="image/png")


async def _solve_gemini(image_b64: str, prompt: str, api_key: str, model: str) -> dict | None:
    """Solve canvas challenge using Google Gemini Vision (free tier)."""
    try:
        from google import genai
    except ImportError:
        return None

    client = genai.Client(api_key=api_key)
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=[_b64_to_gemini_part(image_b64), prompt],
        )
        text = response.text
        return _extract_json(text) if text else None
    except Exception:
        return None


async def _solve_grid_gemini(images_b64: list[str], prompt: str, api_key: str, model: str) -> dict | None:
    """Solve grid challenge using Google Gemini Vision (free tier)."""
    try:
        from google import genai
    except ImportError:
        return None

    # Build content: alternating image parts and labels, then prompt
    contents = []
    for i, img_b64 in enumerate(images_b64):
        contents.append(_b64_to_gemini_part(img_b64))
        contents.append(f"(Image {i})")
    contents.append(prompt)

    client = genai.Client(api_key=api_key)
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
        )
        text = response.text
        return _extract_json(text) if text else None
    except Exception:
        return None
