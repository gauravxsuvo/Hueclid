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

from app.clustering.histogram import build_lab_histogram
from app.color.srgb_lab import lab_to_srgb, linear_to_xyz, srgb_to_linear, xyz_to_lab

_RESIZE_LONG_EDGE = 512


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


def extract_palette(image_bytes: bytes, k: int = 5) -> dict:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_w, orig_h = img.size

    srgb = np.asarray(img, dtype=np.float64) / 255.0
    linear = srgb_to_linear(srgb)
    linear = _resize_linear(linear, _RESIZE_LONG_EDGE)

    lab = xyz_to_lab(linear_to_xyz(linear)).reshape(-1, 3)

    bin_points, weights = build_lab_histogram(lab)

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
    }
