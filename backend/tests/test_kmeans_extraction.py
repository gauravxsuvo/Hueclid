"""Smoke test: extract_palette against a real (synthetic) image.

Builds a fake UI screenshot with four flat-colored regions of different
sizes, runs the full pipeline (decode -> linear resize -> Lab histogram ->
weighted k-means -> Lab-to-sRGB), and checks that what comes out actually
corresponds to what went in: right color count, right rank order by area,
and each recovered color close (in dE00) to the region it came from.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from app.clustering.kmeans import _resize_linear, _select_visualization_points, extract_palette
from app.color.deltae2000 import delta_e2000_matrix
from app.color.srgb_lab import srgb_to_lab

# Four regions, deliberately unequal area so rank order is unambiguous.
# (color, fraction of a 200x200 canvas it covers, via row bands)
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


def test_extract_palette_recovers_known_regions():
    image_bytes = _make_test_image()
    result = extract_palette(image_bytes, k=4)

    assert result["k"] == 4
    assert result["image_size"] == {"width": 200, "height": 200}
    assert len(result["palette"]) == 4

    # Ranked by weight descending: background > blue > black > red,
    # matching the region heights (80 > 60 > 40 > 20).
    weights = [swatch["weight"] for swatch in result["palette"]]
    assert weights == sorted(weights, reverse=True)

    expected_colors = [c for c, _ in _REGIONS]
    expected_lab = srgb_to_lab(np.array(expected_colors, dtype=np.float64))

    recovered_lab = np.array([swatch["lab"] for swatch in result["palette"]])

    # Every recovered swatch should be a close perceptual match to *some*
    # expected region (order isn't required to be identity here, just that
    # each of the four flat colors got recovered by someone).
    dists = delta_e2000_matrix(recovered_lab, expected_lab)  # (4,4)
    best_match = dists.min(axis=1)
    assert np.all(best_match < 2.0), f"dE00 to nearest expected region: {best_match}"

    # And every expected region should have been claimed by some swatch.
    claimed = dists.min(axis=0)
    assert np.all(claimed < 2.0), f"dE00 from expected region to nearest swatch: {claimed}"


def test_extract_palette_hex_and_weight_shape():
    image_bytes = _make_test_image()
    result = extract_palette(image_bytes, k=4)
    for swatch in result["palette"]:
        assert swatch["hex"].startswith("#") and len(swatch["hex"]) == 7
        assert 0.0 <= swatch["weight"] <= 1.0
        assert len(swatch["rgb"]) == 3
        assert all(0 <= v <= 255 for v in swatch["rgb"])

    total_weight = sum(s["weight"] for s in result["palette"])
    assert total_weight == pytest.approx(1.0, abs=1e-6)


def test_extract_palette_k_larger_than_bins_does_not_crash():
    # A single flat-color image has exactly one occupied histogram bin;
    # asking for k=5 clusters must degrade gracefully, not error out.
    img = Image.new("RGB", (50, 50), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = extract_palette(buf.getvalue(), k=5)
    assert result["k"] == 1
    assert len(result["palette"]) == 1
    assert result["palette"][0]["weight"] == pytest.approx(1.0)


def test_visualization_selection_is_bounded_deterministic_and_cluster_aware():
    weights = np.array([100, 90, 80, 70, 60, 50, 4, 3, 2, 1], dtype=np.int64)
    labels = np.array([0, 0, 0, 0, 0, 0, 1, 1, 2, 2], dtype=np.int64)

    first = _select_visualization_points(weights, labels, max_points=6, n_clusters=3)
    second = _select_visualization_points(weights, labels, max_points=6, n_clusters=3)

    np.testing.assert_array_equal(first, second)
    assert first.shape == (6,)
    assert set(labels[first]) == {0, 1, 2}
    assert 0 in first  # heaviest global point
    assert 6 in first  # heaviest point in the small second cluster
    assert 8 in first  # heaviest point in the small third cluster


def test_linear_resize_clips_lanczos_ringing_to_physical_rgb_range():
    linear = np.ones((64, 513, 3), dtype=np.float64)
    linear[:, 255:257] = 0.0

    resized = _resize_linear(linear, target_long_edge=512)

    assert resized.min() >= 0.0
    assert resized.max() <= 1.0
