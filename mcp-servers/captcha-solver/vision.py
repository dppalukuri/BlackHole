"""
Vision engine - Uses CLIP for zero-shot image classification.

CLIP (Contrastive Language-Image Pre-Training) matches images to text descriptions.
Perfect for CAPTCHA challenges like "select all images containing a bus".

Model: openai/clip-vit-base-patch32 (~350MB, downloads on first use)
Runs on CPU, no GPU required.
"""

import io
import base64
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# Singleton model instance
_model = None
_processor = None

MODEL_NAME = "openai/clip-vit-base-patch32"


def _load_model():
    """Load CLIP model (lazy, cached after first call)."""
    global _model, _processor
    if _model is None:
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _model.eval()
    return _model, _processor


def load_image(source: str | bytes) -> Image.Image:
    """Load image from base64 string, URL, or file path."""
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source)).convert("RGB")

    if source.startswith("data:image"):
        # data:image/png;base64,iVBOR...
        b64_data = source.split(",", 1)[1]
        return Image.open(io.BytesIO(base64.b64decode(b64_data))).convert("RGB")

    if source.startswith("http://") or source.startswith("https://"):
        import httpx
        resp = httpx.get(
            source, timeout=15, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"}
        )
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")

    # File path
    return Image.open(source).convert("RGB")


def classify_image(image: Image.Image, labels: list[str]) -> dict[str, float]:
    """
    Classify an image against a list of text labels.

    Returns dict of {label: probability} sorted by probability descending.
    """
    model, processor = _load_model()

    inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=0)

    results = {label: float(prob) for label, prob in zip(labels, probs)}
    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))


def classify_images_batch(
    images: list[Image.Image],
    target_label: str,
    negative_labels: list[str] | None = None,
    threshold: float = 0.5,
) -> list[dict]:
    """
    Classify multiple images as matching or not matching a target label.

    Uses multiple negative labels for more robust classification.

    Args:
        images: List of PIL images
        target_label: What to look for (e.g., "a bus", "a traffic light")
        negative_labels: Counter-labels (default: common CAPTCHA distractors)
        threshold: Minimum probability to consider a match

    Returns:
        List of dicts with {index, match, confidence} for each image
    """
    model, processor = _load_model()

    if negative_labels is None:
        negative_labels = [
            "a car on a road",
            "a building",
            "a tree or plant",
            "a person walking",
            "an empty street",
            "a landscape or scenery",
        ]

    all_labels = [target_label] + negative_labels

    results = []
    for i, img in enumerate(images):
        inputs = processor(text=all_labels, images=img, return_tensors="pt", padding=True)

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0)

        target_prob = float(probs[0])
        results.append({
            "index": i,
            "match": target_prob >= threshold,
            "confidence": target_prob,
        })

    return results


def match_image_to_text(image: Image.Image, text: str) -> float:
    """
    Get similarity score between an image and a text description.

    Returns a probability (0-1) of how well the image matches the text.
    """
    result = classify_image(image, [text, "something completely different"])
    return result[text]
