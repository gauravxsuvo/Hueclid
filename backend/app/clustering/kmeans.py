"""Weighted Lab k-means palette extraction -- the vertical-slice baseline.

This is the Euclidean-in-Lab arm, not the dE00 k-medoids method (PLAN.md
2.4a, phase weeks 7-9). It exists so the API has a real, working endpoint
from week 1 while the perceptually-correct clustering is still being built.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from app.cache.histogram_cache import get_cached_bins, hash_image_bytes, store_bins
from app.clustering.histogram import build_lab_histogram
from app.clustering.image_prep import (
    RESIZE_LONG_EDGE,
    ImageTooLargeError,  # noqa: F401 -- re-exported, `app.api.extract` imports it from here
    decode_rgb,
    resize_linear,
)
from app.color.srgb_lab import lab_to_srgb, linear_to_xyz, srgb_to_linear, xyz_to_lab

# The Lab histogram grid (PLAN.md 2.4a). Cache entries are keyed on the
# image hash but only reused if they were binned at this same grid.
_L_STEP = 2.0
_A_STEP = 2.0
_B_STEP = 2.0


def _to_hex(rgb_255: np.ndarray) -> str:
    r, g, b = (int(round(v)) for v in rgb_255)
    return f"#{r:02x}{g:02x}{b:02x}"


def compute_lab_bins(image_bytes: bytes, db_session=None) -> dict:
    """Decode + linear-light resize + Lab histogram binning, or a cache hit.

    This is the deterministic, cacheable half of the pipeline (PLAN.md
    4.3): shared by extract_palette and by dataset ingestion, which only
    needs the bins, not a clustered palette.
    """
    image_hash = hash_image_bytes(image_bytes)

    cached = None
    if db_session is not None:
        cached = get_cached_bins(db_session, image_hash, _L_STEP, _A_STEP, _B_STEP)

    if cached is not None:
        bin_points, weights, orig_w, orig_h = cached
    else:
        img, (orig_w, orig_h) = decode_rgb(image_bytes)

        srgb = np.asarray(img, dtype=np.float64) / 255.0
        linear = srgb_to_linear(srgb)
        linear = resize_linear(linear, RESIZE_LONG_EDGE)

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

    return {
        "image_hash": image_hash,
        "bin_points": bin_points,
        "weights": weights,
        "width": orig_w,
        "height": orig_h,
        "cache_hit": cached is not None,
    }


def extract_palette(image_bytes: bytes, k: int = 5, db_session=None) -> dict:
    bins = compute_lab_bins(image_bytes, db_session=db_session)
    bin_points, weights = bins["bin_points"], bins["weights"]
    orig_w, orig_h = bins["width"], bins["height"]

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
        "cache_hit": bins["cache_hit"],
    }
