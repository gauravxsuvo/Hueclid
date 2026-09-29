"""Shared image decode + linear-light resize, used by every clustering arm.

Pulled out of `kmeans.py` (the Lab arm) so the Oklab arm (`oklab_kmeans.py`)
gets the same bug-fixed handling for free instead of a second copy that can
drift: the alpha-composite-onto-white fix (issue #19) and the draft-decode
OOM guard (issue #29) both live here now, exactly once.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

# Downscale target for the real, quality-affecting resize, done in linear
# light (PLAN.md 2.4a) so averaging doesn't darken/desaturate the result.
RESIZE_LONG_EDGE = 512

# Only changes the cost of decoding a JPEG, not what it looks like: libjpeg
# can DCT-scale straight to roughly this size, well above RESIZE_LONG_EDGE
# so the real downscale still happens in linear light below (issue #29 -- a
# 48MP phone photo was being decoded and converted to float64 at full
# resolution before ever being resized).
_DRAFT_LONG_EDGE = 1024

# Backstop for formats draft() can't shrink during decode (PNG, WEBP): a
# ceiling on decoded pixel count so an oversized upload gets a clear
# rejection instead of an out-of-memory crash.
_MAX_DECODE_PIXELS = 40_000_000


class ImageTooLargeError(ValueError):
    """Decoded image exceeds the pixel budget the pipeline can convert to
    float in memory (issue #29)."""


def decode_rgb(image_bytes: bytes) -> tuple[Image.Image, tuple[int, int]]:
    """Decode the upload to a flat RGB image.

    Pillow's `.convert("RGB")` on an image with an alpha channel doesn't
    composite, it just drops the alpha channel and keeps whatever RGB
    values happen to be stored underneath each pixel. For a lot of real
    PNGs (logos, icons, cutouts) that's black, so a fully transparent
    background silently became a real, heavily-weighted "color" in the
    output palette (issue #19). Compositing onto a white backing first
    makes a transparent pixel contribute white, the same as it would
    render in a browser over a light page, and a partially transparent
    one blends toward white instead of keeping its hidden raw value.

    Returns the flat RGB image plus its size *before* the JPEG draft
    scaling below, since that's the resolution the caller wants to report.
    """
    img = Image.open(io.BytesIO(image_bytes))
    orig_size = img.size

    # No-op for anything that isn't JPEG/MPO; safe to call unconditionally.
    img.draft("RGB", (_DRAFT_LONG_EDGE, _DRAFT_LONG_EDGE))

    if img.width * img.height > _MAX_DECODE_PIXELS:
        raise ImageTooLargeError(
            f"Image resolution too large ({img.width}x{img.height}px, "
            f"max {_MAX_DECODE_PIXELS // 1_000_000} megapixels)"
        )

    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        img = img.convert("RGBA")
        backing = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(backing, img)
    return img.convert("RGB"), orig_size


def resize_linear(linear_rgb: np.ndarray, target_long_edge: int = RESIZE_LONG_EDGE) -> np.ndarray:
    """Resize an (H,W,3) linear-light float array, decoded before resampling
    so downscaling doesn't darken/desaturate (PLAN.md 2.4a preprocessing note).
    """
    h, w = linear_rgb.shape[:2]
    long_edge = max(h, w)
    if long_edge <= target_long_edge:
        return linear_rgb

    scale = target_long_edge / long_edge
    new_w, new_h = max(1, round(w * scale)), max(1, round(h * scale))

    channels = []
    for c in range(3):
        im = Image.fromarray(linear_rgb[..., c].astype(np.float32), mode="F")
        im = im.resize((new_w, new_h), Image.LANCZOS)
        channels.append(np.asarray(im, dtype=np.float64))
    return np.stack(channels, axis=-1)
