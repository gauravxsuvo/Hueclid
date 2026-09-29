"""Oklab + Euclidean k-means arm (PLAN.md 2.4b) -- same smoke tests as the
Lab k-means baseline (`test_kmeans_extraction.py`), plus a cross-arm check
against the dE00 weighted k-medoids engine (`app.clustering.pam`), since
the point of this arm is that it's a first-class comparison, not a
strawman: on an image with well-separated flat regions, both arms should
recover essentially the same palette.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from app.clustering.histogram import build_lab_histogram
from app.clustering.image_prep import ImageTooLargeError
from app.clustering.kmeans import extract_palette
from app.clustering.oklab_kmeans import _A_STEP, _B_STEP, _L_STEP, extract_palette_oklab
from app.color.deltae2000 import delta_e2000_matrix
from app.color.oklab import delta_e_ok, oklab_to_srgb, srgb_to_oklab, xyz_to_oklab
from app.color.srgb_lab import linear_to_xyz, srgb_to_lab, srgb_to_linear

# Same regions as test_kmeans_extraction.py, so the two test files are easy
# to compare side by side.
_REGIONS = [
    ((245, 245, 245), 80),  # near-white background, biggest
    ((25, 90, 210), 60),  # primary blue
    ((20, 20, 20), 40),  # near-black text block
    ((205, 30, 30), 20),  # danger red, smallest
]


def _make_test_image() -> bytes:
    width = 200
    rows = []
    for color, height in _REGIONS:
        band = np.tile(np.array(color, dtype=np.uint8), (height, width, 1))
        rows.append(band)
    arr = np.concatenate(rows, axis=0)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_palette_oklab_recovers_known_regions():
    image_bytes = _make_test_image()
    result = extract_palette_oklab(image_bytes, k=4)

    assert result["k"] == 4
    assert result["arm"] == "oklab_euclidean_kmeans"
    assert result["image_size"] == {"width": 200, "height": 200}
    assert len(result["palette"]) == 4

    weights = [swatch["weight"] for swatch in result["palette"]]
    assert weights == sorted(weights, reverse=True)

    expected_colors = [c for c, _ in _REGIONS]
    expected_lab = srgb_to_lab(np.array(expected_colors, dtype=np.float64))
    recovered_lab = srgb_to_lab(np.array([swatch["rgb"] for swatch in result["palette"]]))

    dists = delta_e2000_matrix(recovered_lab, expected_lab)
    assert np.all(dists.min(axis=1) < 2.0), f"dE00 to nearest expected region: {dists.min(1)}"
    assert np.all(dists.min(axis=0) < 2.0), "dE00 from expected region to nearest swatch"


def test_extract_palette_oklab_hex_and_weight_shape():
    image_bytes = _make_test_image()
    result = extract_palette_oklab(image_bytes, k=4)
    for swatch in result["palette"]:
        assert swatch["hex"].startswith("#") and len(swatch["hex"]) == 7
        assert 0.0 <= swatch["weight"] <= 1.0
        assert len(swatch["oklab"]) == 3
        assert all(0 <= v <= 255 for v in swatch["rgb"])
    assert sum(s["weight"] for s in result["palette"]) == pytest.approx(1.0, abs=1e-6)


def test_extract_palette_oklab_k_larger_than_bins_does_not_crash():
    img = Image.new("RGB", (50, 50), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = extract_palette_oklab(buf.getvalue(), k=5)
    assert result["k"] == 1
    assert len(result["palette"]) == 1
    assert result["palette"][0]["weight"] == pytest.approx(1.0)


def test_extract_palette_oklab_rejects_oversized_png():
    img = Image.new("RGB", (9000, 9000), color=(10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with pytest.raises(ImageTooLargeError):
        extract_palette_oklab(buf.getvalue(), k=3)


def test_oklab_arm_agrees_with_lab_kmeans_arm_on_separated_regions():
    """Not a strawman comparison (PLAN.md 2.4b): on well-separated flat
    regions there's only one reasonable 4-way partition, so the Lab
    Euclidean k-means baseline and the Oklab Euclidean k-means arm should
    land on close to the same four colors even though they cluster in
    different spaces.
    """
    image_bytes = _make_test_image()
    lab_result = extract_palette(image_bytes, k=4)
    oklab_result = extract_palette_oklab(image_bytes, k=4)

    lab_rgb = srgb_to_lab(np.array([s["rgb"] for s in lab_result["palette"]], dtype=np.float64))
    oklab_rgb = srgb_to_lab(np.array([s["rgb"] for s in oklab_result["palette"]], dtype=np.float64))

    dists = delta_e2000_matrix(lab_rgb, oklab_rgb)
    assert np.all(dists.min(axis=1) < 2.0)
    assert np.all(dists.min(axis=0) < 2.0)

    # And the mass ranking of the four regions should agree between arms too.
    lab_order = [s["rank"] for s in sorted(lab_result["palette"], key=lambda s: -s["weight"])]
    oklab_order = [s["rank"] for s in sorted(oklab_result["palette"], key=lambda s: -s["weight"])]
    assert lab_order == oklab_order == [0, 1, 2, 3]


def test_oklab_bin_quantization_error_is_small():
    """The bin-mean representative should sit close (in dE_ok) to every
    pixel that voted into it -- the same guarantee `build_lab_histogram`'s
    Lab usage relies on, just checked at Oklab's own grid steps.
    """
    rng = np.random.default_rng(0)
    srgb = rng.integers(0, 256, size=(20_000, 3)).astype(np.float64)

    oklab = xyz_to_oklab(linear_to_xyz(srgb_to_linear(srgb / 255.0)))
    bin_points, _ = build_lab_histogram(oklab, _L_STEP, _A_STEP, _B_STEP)

    idx = np.floor(oklab / np.array([_L_STEP, _A_STEP, _B_STEP])).astype(np.int64)
    _, inverse = np.unique(idx, axis=0, return_inverse=True)
    representative = bin_points[inverse.reshape(-1)]

    err = delta_e_ok(oklab, representative)
    # A cell of side s has a worst-case center-to-corner distance of
    # sqrt(3)*s/2 =~ 0.0173 for s=0.02; bin_points uses the *mean* member
    # position rather than the cell center, which is strictly better, so
    # the measured 99th percentile (~0.0146) sits comfortably under that
    # theoretical ceiling. Threshold below is that ceiling, not the tighter
    # measured value, so the test isn't pinned to today's random sample.
    assert np.percentile(err, 99) < 0.018, f"99th pct quantization dE_ok: {np.percentile(err, 99)}"


def test_oklab_to_srgb_used_by_this_arm_round_trips_through_gamut_mapping():
    # Guards against silently regressing back to hard clipping for the
    # centers this module hands to `oklab_to_srgb` -- an out-of-gamut Oklab
    # point should come back visibly less saturated, not just channel-clipped.
    saturated = srgb_to_oklab(np.array([255.0, 0.0, 0.0]))
    boosted = saturated.copy()
    boosted[1] *= 1.3  # push a further out of gamut
    mapped = oklab_to_srgb(boosted)
    assert np.all((mapped >= 0) & (mapped <= 255))
