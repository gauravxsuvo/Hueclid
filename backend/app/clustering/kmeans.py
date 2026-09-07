"""Weighted Lab k-means palette extraction -- the vertical-slice baseline.

This is the Euclidean-in-Lab arm, not the dE00 k-medoids method (PLAN.md
2.4a, phase weeks 7-9). It exists so the API has a real, working endpoint
from week 1 while the perceptually-correct clustering is still being built.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from app.cache.histogram_cache import get_cached_bins, hash_image_bytes, store_bins
from app.clustering.histogram import build_lab_histogram
from app.color.srgb_lab import lab_to_srgb, linear_to_xyz, srgb_to_linear, xyz_to_lab

_RESIZE_LONG_EDGE = 512

# The Lab histogram grid (PLAN.md 2.4a). Cache entries are keyed on the
# image hash but only reused if they were binned at this same grid.
_L_STEP = 2.0
_A_STEP = 2.0
_B_STEP = 2.0

# Only changes the cost of decoding a JPEG, not what it looks like: libjpeg
# can DCT-scale straight to roughly this size, well above _RESIZE_LONG_EDGE
# so the real, quality-affecting downscale still happens in linear light in
# _resize_linear below (issue #29 -- a 48MP phone photo was being decoded
# and converted to float64 at full resolution before ever being resized).
_DRAFT_LONG_EDGE = 1024

# Backstop for formats draft() can't shrink during decode (PNG, WEBP): a
# ceiling on decoded pixel count so an oversized upload gets a clear
# rejection instead of an out-of-memory crash.
_MAX_DECODE_PIXELS = 40_000_000


class ImageTooLargeError(ValueError):
    """Decoded image exceeds the pixel budget the pipeline can convert to
    float in memory (issue #29)."""


def _decode_rgb(image_bytes: bytes) -> tuple[Image.Image, tuple[int, int]]:
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


def _resize_linear(linear_rgb: np.ndarray, target_long_edge: int) -> np.ndarray:
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


def _to_hex(rgb_255: np.ndarray) -> str:
    r, g, b = (int(round(v)) for v in rgb_255)
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_palette(image_bytes: bytes, k: int = 5, db_session=None) -> dict:
    image_hash = hash_image_bytes(image_bytes)

    cached = None
    if db_session is not None:
        cached = get_cached_bins(db_session, image_hash, _L_STEP, _A_STEP, _B_STEP)

    if cached is not None:
        bin_points, weights, orig_w, orig_h = cached
    else:
        img, (orig_w, orig_h) = _decode_rgb(image_bytes)

        srgb = np.asarray(img, dtype=np.float64) / 255.0
        linear = srgb_to_linear(srgb)
        linear = _resize_linear(linear, _RESIZE_LONG_EDGE)

        lab = xyz_to_lab(linear_to_xyz(linear)).reshape(-1, 3)

        bin_points, weights = build_lab_histogram(lab, _L_STEP, _A_STEP, _B_STEP)

        if db_session is not None:
            store_bins(
                db_session,
                image_hash,
                bin_points,
                weights,
                orig_w,
                orig_h,
                _L_STEP,
                _A_STEP,
                _B_STEP,
            )

    n_clusters = min(k, bin_points.shape[0])
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=0)
    km.fit(bin_points, sample_weight=weights)

    centers = km.cluster_centers_
    labels = km.labels_
    cluster_mass = np.zeros(n_clusters, dtype=np.float64)
    np.add.at(cluster_mass, labels, weights)
    total_mass = cluster_mass.sum()

    order = np.argsort(-cluster_mass)

    palette = []
    for rank, ci in enumerate(order):
        lab_center = centers[ci]
        rgb_255 = lab_to_srgb(lab_center)
        palette.append(
            {
                "rank": rank,
                "hex": _to_hex(rgb_255),
                "rgb": [int(round(v)) for v in rgb_255],
                "lab": [round(float(v), 4) for v in lab_center],
                "weight": round(float(cluster_mass[ci] / total_mass), 6),
            }
        )

    return {
        "palette": palette,
        "k": n_clusters,
        "image_size": {"width": orig_w, "height": orig_h},
        "histogram_bins": int(bin_points.shape[0]),
        "cache_hit": cached is not None,
    }
