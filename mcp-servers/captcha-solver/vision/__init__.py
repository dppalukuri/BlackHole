"""Vision engine package — re-exports from submodules for backward compatibility."""

from vision.clip import (
    _load_model,
    load_image,
    classify_image,
    classify_images_batch,
    get_image_embeddings,
    match_image_to_text,
)
