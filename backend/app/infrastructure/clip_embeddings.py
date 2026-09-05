"""CLIP image embeddings for image-based product search.

Uses openai/clip-vit-base-patch32 via transformers - loaded locally, no API key required. CLIP's vision
encoder projects any image into a 512-dim vector (verified: `model.config.projection_dim == 512`) such that
visually/semantically similar images land close together, which is exactly the property pgvector's cosine
search over Product.image_embedding relies on.

API note: in current transformers versions, `CLIPModel.get_image_features(...)` returns a
`BaseModelOutputWithPooling`, not a bare tensor as in older releases/tutorials - the actual 512-dim
embedding is `.pooler_output` (`.last_hidden_state` is the pre-projection 768-dim per-patch sequence, not
what you want here). Verified directly against the installed model rather than assumed from memory, since
this is exactly the kind of API drift that breaks copy-pasted CLIP tutorials.
"""
import io
import os
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # works around a transient 403 from HF's Xet CDN for this repo

from PIL import Image
from typing import Any

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIMENSIONS = 512

_model: Any | None = None
_processor: Any | None = None


def _load() -> tuple[Any, Any]:
    """torch/transformers are imported here, not at module level - this module is pulled in at API startup
    (via services/image_search.py), and those two imports alone are slow enough on a CPU-constrained
    deployment (e.g. Render's free tier) to blow past the platform's port-binding timeout. Deferring them to
    first actual use means the API can start immediately and only pays that cost on the first image search."""
    global _model, _processor
    if _model is None or _processor is None:
        import torch  # noqa: F401 (imported for its side effect of registering torch backends transformers needs)
        from transformers import CLIPModel, CLIPProcessor
        _model = CLIPModel.from_pretrained(MODEL_NAME).eval()
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    return _model, _processor


def embed_image(image_bytes: bytes) -> list[float]:
    """Embed one image (any common format - JPEG/PNG/WEBP/etc.) into a 512-dim, L2-normalized vector."""
    import torch
    model, processor = _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=[image], return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs).pooler_output
        features = features / features.norm(dim=-1, keepdim=True)
    return features[0].tolist()


def embed_images(images: list[bytes]) -> list[list[float]]:
    """Batch version of embed_image, for indexing many product photos at once."""
    import torch
    model, processor = _load()
    pil_images = [Image.open(io.BytesIO(data)).convert("RGB") for data in images]
    inputs = processor(images=pil_images, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs).pooler_output
        features = features / features.norm(dim=-1, keepdim=True)
    return features.tolist()
