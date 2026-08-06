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


def _select_visualization_points(
    weights: np.ndarray,
    labels: np.ndarray,
    max_points: int,
    n_clusters: int,
) -> np.ndarray:
    """Choose a deterministic, cluster-aware subset of histogram bins.

    The heaviest bins carry most of the visual signal, but a purely global top-N
    can erase a small accent cluster. Reserve a small quota per cluster first,
    then fill the remaining budget by weight across the whole image.
    """
    n_points = weights.shape[0]
    if n_points <= max_points:
        return np.arange(n_points, dtype=np.int64)

    guaranteed_per_cluster = max(1, min(16, max_points // (2 * n_clusters)))
    selected: list[int] = []
    selected_mask = np.zeros(n_points, dtype=bool)

    for cluster_index in range(n_clusters):
        cluster_points = np.flatnonzero(labels == cluster_index)
        cluster_order = np.lexsort((cluster_points, -weights[cluster_points]))
        chosen = cluster_points[cluster_order[:guaranteed_per_cluster]]
        selected.extend(chosen.tolist())
        selected_mask[chosen] = True

    remaining_budget = max_points - len(selected)
    if remaining_budget > 0:
        candidates = np.flatnonzero(~selected_mask)
        candidate_order = np.lexsort((candidates, -weights[candidates]))
        selected.extend(candidates[candidate_order[:remaining_budget]].tolist())

    selected_array = np.asarray(selected, dtype=np.int64)
    final_order = np.lexsort((selected_array, -weights[selected_array]))
    return selected_array[final_order]


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
    # Lanczos is not range-preserving around hard edges: its negative lobes can
    # ring below black or above white. Those values are not physical RGB and can
    # otherwise yield impossible CIELAB values (for example L* < 0).
    return np.clip(np.stack(channels, axis=-1), 0.0, 1.0)


def _to_hex(rgb_255: np.ndarray) -> str:
    r, g, b = (int(round(v)) for v in rgb_255)
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_palette(
    image_bytes: bytes,
    k: int = 5,
    *,
    include_points: bool = False,
    max_points: int = 4000,
) -> dict:
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
    rank_for_cluster = np.empty(n_clusters, dtype=np.int64)
    rank_for_cluster[order] = np.arange(n_clusters)

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

    result = {
        "palette": palette,
        "k": n_clusters,
        "image_size": {"width": orig_w, "height": orig_h},
        "histogram_bins": int(bin_points.shape[0]),
    }

    if include_points:
        selected = _select_visualization_points(weights, labels, max_points, n_clusters)
        selected_lab = bin_points[selected]
        selected_rgb = lab_to_srgb(selected_lab)
        point_cluster_ranks = rank_for_cluster[labels[selected]]

        points = []
        for lab_point, rgb_point, point_weight, cluster_rank in zip(
            selected_lab,
            selected_rgb,
            weights[selected],
            point_cluster_ranks,
            strict=True,
        ):
            points.append(
                {
                    "lab": [round(float(v), 4) for v in lab_point],
                    "rgb": [int(round(v)) for v in rgb_point],
                    "weight": round(float(point_weight / total_mass), 8),
                    "cluster": int(cluster_rank),
                }
            )

        result["visualization"] = {
            "schema_version": 1,
            "space": "cielab-d65",
            "axes": {"x": "a*", "y": "L*", "z": "b*"},
            "points": points,
            "total_bins": int(bin_points.shape[0]),
            "displayed_bins": int(selected.shape[0]),
            "displayed_weight": round(float(weights[selected].sum() / total_mass), 8),
            "truncated": bool(selected.shape[0] < bin_points.shape[0]),
        }

    return result
