"""Oklab + weighted Euclidean k-means -- the comparison arm PLAN.md 2.4b
calls for, not a strawman: Oklab is a genuine metric space, so the
arithmetic mean is the exact minimizer of summed squared distance and
Lloyd's algorithm keeps every one of its usual guarantees, at a fraction
of the cost of dE00 k-medoids (`app.clustering.pam`). Do not assume the
dE00 arm wins; PLAN.md 2.4b is explicit that if this arm matches it at a
fraction of the runtime, that is itself a publishable finding.

Shares image decode/resize with the Lab arm (`app.clustering.image_prep`)
and the generic grid-binning routine (`app.clustering.histogram`) -- that
routine has no Lab-specific math, it floor-divides whatever (N,3) points
it is given, so the same "bin, don't sample" approach (PLAN.md 2.4a)
applies here unchanged, just gridded in Oklab's own coordinate range.
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from app.clustering.histogram import build_lab_histogram
from app.clustering.image_prep import RESIZE_LONG_EDGE, decode_rgb, resize_linear
from app.color.oklab import oklab_to_srgb, xyz_to_oklab
from app.color.srgb_lab import linear_to_xyz, srgb_to_linear

# Oklab's L is [0, 1] and a/b span roughly [-0.3, 0.3] for in-gamut sRGB,
# a much smaller range than CIELAB's, so these steps are not a like-for-like
# rescale of the Lab grid's (PLAN.md 2.4a: L/a/b all step 2 over ranges of
# ~100-256) -- they're chosen directly so quantization error stays small in
# Oklab's own units, checked in test_oklab_bin_quantization_error_is_small
# against the theoretical per-cell ceiling (sqrt(3)*step/2). Bin points are
# the mean position of their members (see `build_lab_histogram`), which is
# the exact per-bin quantization-error minimizer in a Euclidean space --
# doubly so here, since Oklab's whole premise is that Euclidean distance
# already is the perceptual one.
_L_STEP = 0.02
_A_STEP = 0.02
_B_STEP = 0.02


def _to_hex(rgb_255: np.ndarray) -> str:
    r, g, b = (int(round(v)) for v in rgb_255)
    return f"#{r:02x}{g:02x}{b:02x}"


def compute_oklab_bins(image_bytes: bytes) -> dict:
    """Decode + linear-light resize + Oklab histogram binning.

    Mirrors `app.clustering.kmeans.compute_lab_bins` but has no cache
    parameter: the Postgres cache (PLAN.md 4.3) is keyed on the Lab grid
    only for now, since this arm is a comparison baseline, not the wired-up
    API path. Revisit if/when this arm is exposed through the endpoint.
    """
    img, (orig_w, orig_h) = decode_rgb(image_bytes)

    srgb = np.asarray(img, dtype=np.float64) / 255.0
    linear = srgb_to_linear(srgb)
    linear = resize_linear(linear, RESIZE_LONG_EDGE)

    oklab = xyz_to_oklab(linear_to_xyz(linear)).reshape(-1, 3)
    bin_points, weights = build_lab_histogram(oklab, _L_STEP, _A_STEP, _B_STEP)

    return {
        "bin_points": bin_points,
        "weights": weights,
        "width": orig_w,
        "height": orig_h,
    }


def cluster_oklab_kmeans(
    oklab_points: np.ndarray,
    weights: np.ndarray,
    k: int,
    random_state: int = 0,
) -> KMeans:
    """Weighted Euclidean k-means over Oklab points. A thin wrapper: the
    guarantee that makes this arm valid (mean == minimizer) is Oklab's
    construction, not anything this function does -- see the module
    docstring and `app.color.oklab.delta_e_ok`.
    """
    n_clusters = min(k, oklab_points.shape[0])
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=random_state)
    km.fit(oklab_points, sample_weight=weights)
    return km


def extract_palette_oklab(image_bytes: bytes, k: int = 5) -> dict:
    """Same shape of result as `app.clustering.kmeans.extract_palette`, so
    the two arms are directly comparable: same ranking rule (by cluster
    mass), same palette schema, with `lab` replaced by `oklab`.
    """
    bins = compute_oklab_bins(image_bytes)
    bin_points, weights = bins["bin_points"], bins["weights"]
    orig_w, orig_h = bins["width"], bins["height"]

    km = cluster_oklab_kmeans(bin_points, weights, k)
    n_clusters = km.n_clusters
    centers = km.cluster_centers_
    labels = km.labels_

    cluster_mass = np.zeros(n_clusters, dtype=np.float64)
    np.add.at(cluster_mass, labels, weights)
    total_mass = cluster_mass.sum()

    order = np.argsort(-cluster_mass)

    palette = []
    for rank, ci in enumerate(order):
        oklab_center = centers[ci]
        rgb_255 = oklab_to_srgb(oklab_center)
        palette.append(
            {
                "rank": rank,
                "hex": _to_hex(rgb_255),
                "rgb": [int(round(v)) for v in rgb_255],
                "oklab": [round(float(v), 6) for v in oklab_center],
                "weight": round(float(cluster_mass[ci] / total_mass), 6),
            }
        )

    return {
        "palette": palette,
        "k": n_clusters,
        "image_size": {"width": orig_w, "height": orig_h},
        "histogram_bins": int(bin_points.shape[0]),
        "arm": "oklab_euclidean_kmeans",
    }
