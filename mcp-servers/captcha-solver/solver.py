"""
CAPTCHA solving logic - extracts challenges from pages and solves with CLIP.

Supports:
  - hCaptcha image grid challenges
  - reCAPTCHA v2 image challenges
"""

import asyncio
import re
import base64
import io
from PIL import Image

from vision import load_image, classify_images_batch, match_image_to_text


# Common hCaptcha task mappings to improve CLIP accuracy
TASK_REWRITES = {
    "motorbus": "a bus on a road",
    "bus": "a bus on a road",
    "airplane": "an airplane in the sky",
    "motorcycle": "a motorcycle",
    "bicycle": "a bicycle",
    "boat": "a boat on water",
    "traffic light": "a traffic light",
    "fire hydrant": "a fire hydrant on a street",
    "stop sign": "a stop sign",
    "parking meter": "a parking meter",
    "horse": "a horse",
    "elephant": "an elephant",
    "bear": "a bear",
    "zebra": "a zebra",
    "giraffe": "a giraffe",
    "dog": "a dog",
    "cat": "a cat",
    "bird": "a bird",
    "train": "a train on tracks",
    "truck": "a truck on a road",
    "car": "a car on a road",
    "bridge": "a bridge",
    "chimney": "a chimney on a roof",
    "crosswalk": "a crosswalk or pedestrian crossing",
    "staircase": "a staircase or stairs",
    "bedroom": "a bedroom with a bed",
    "living room": "a living room",
    "kitchen": "a kitchen with appliances",
    "bathroom": "a bathroom",
    "swimming pool": "a swimming pool",
    "seaplane": "a seaplane on water",
    "vertical river": "a river flowing vertically",
}


def enhance_task_text(raw_task: str) -> str:
    """
    Improve the CAPTCHA task text for better CLIP classification.

    hCaptcha tasks look like: "Please click each image containing a motorbus"
    We extract the target object and optionally rewrite for CLIP.
    """
    # Extract the target object from common phrasings
    patterns = [
        r"containing (?:a |an )?(.+?)\.?$",
        r"with (?:a |an )?(.+?)\.?$",
        r"showing (?:a |an )?(.+?)\.?$",
        r"select (?:all )?(?:images? )?(?:of |with )?(?:a |an )?(.+?)\.?$",
        r"click (?:on )?(?:each |all )?(?:images? )?(?:containing |with |of )?(?:a |an )?(.+?)\.?$",
    ]

    target = raw_task.lower().strip()
    for pattern in patterns:
        match = re.search(pattern, target, re.I)
        if match:
            target = match.group(1).strip()
            break

    # Check if we have a better description for CLIP
    if target in TASK_REWRITES:
        return TASK_REWRITES[target]

    # Default: prefix with "a photo of"
    if not target.startswith(("a ", "an ", "the ")):
        target = f"a {target}"

    return target


async def solve_hcaptcha_challenge(
    task_text: str,
    image_data: list[str],
    threshold: float = 0.55,
) -> dict:
    """
    Solve an hCaptcha image grid challenge.

    Args:
        task_text: The challenge instruction (e.g., "Please click each image containing a motorbus")
        image_data: List of image data (base64 strings or URLs)
        threshold: Confidence threshold for matching (0-1)

    Returns:
        {
            "task": original task,
            "target": enhanced target description,
            "selections": [index list of matching images],
            "details": [{index, match, confidence}, ...],
        }
    """
    target = enhance_task_text(task_text)

    # Load all images
    images = []
    for src in image_data:
        try:
            img = load_image(src)
            images.append(img)
        except Exception:
            # Create a blank image as placeholder for failed loads
            images.append(Image.new("RGB", (100, 100), (128, 128, 128)))

    if not images:
        return {"task": task_text, "target": target, "selections": [], "details": []}

    # Classify all images against the target
    results = await asyncio.to_thread(
        classify_images_batch,
        images,
        target_label=target,
        threshold=threshold,
    )

    selections = [r["index"] for r in results if r["match"]]

    # If no selections, lower threshold and try again
    if not selections and results:
        best = max(results, key=lambda r: r["confidence"])
        if best["confidence"] > 0.35:
            selections = [best["index"]]

    return {
        "task": task_text,
        "target": target,
        "selections": selections,
        "details": results,
    }


async def solve_recaptcha_challenge(
    task_text: str,
    image_data: list[str],
    threshold: float = 0.55,
) -> dict:
    """
    Solve a reCAPTCHA v2 image challenge.

    Same approach as hCaptcha - extract target from task, classify images.
    """
    # reCAPTCHA tasks are similar: "Select all images with crosswalks"
    return await solve_hcaptcha_challenge(task_text, image_data, threshold)


async def classify_single_image(
    image_data: str,
    labels: list[str],
) -> dict:
    """
    Classify a single image against a list of labels.

    Args:
        image_data: Base64 string or URL of the image
        labels: List of text descriptions to match against

    Returns:
        {label: probability} sorted by probability descending
    """
    from vision import classify_image

    img = load_image(image_data)
    results = await asyncio.to_thread(classify_image, img, labels)
    return results
