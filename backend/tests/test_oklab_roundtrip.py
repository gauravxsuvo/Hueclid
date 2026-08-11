"""Property tests for Oklab: round-trips, vectorization, metric behavior.

The companion to `test_srgb_lab_roundtrip.py`, same shape of guarantee for
the second color space. Where the CIELAB suite bounds its round-trip error
in dE00, this one bounds it in raw Oklab units, because in Oklab plain
Euclidean distance *is* the perceptual distance (PLAN.md 2.2) -- that is
the property the whole space exists for, so it is also what gets asserted.
"""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from app.color.oklab import (
    delta_e_ok,
    oklab_to_oklch,
    oklab_to_srgb,
    oklab_to_xyz,
    oklch_to_oklab,
    srgb_to_oklab,
    xyz_to_oklab,
)

rgb_byte = st.integers(min_value=0, max_value=255)


@settings(max_examples=1000, deadline=None)
@given(r=rgb_byte, g=rgb_byte, b=rgb_byte)
def test_roundtrip_single_pixel(r, g, b):
    original = np.array([r, g, b], dtype=np.float64)
    recovered = oklab_to_srgb(srgb_to_oklab(original))
    assert np.max(np.abs(recovered - original)) < 0.01


def test_roundtrip_batch_10000_max_delta_ok():
    rng = np.random.default_rng(42)
    original = rng.integers(0, 256, size=(10_000, 3)).astype(np.float64)
    oklab = srgb_to_oklab(original)
    recovered = srgb_to_oklab(oklab_to_srgb(oklab))
    max_de = np.max(delta_e_ok(oklab, recovered))
    assert max_de < 1e-9, f"max Oklab round-trip error = {max_de}"


def test_xyz_roundtrip_is_exact_to_float64():
    """No clipping, no gamut mapping in this path, so it should be near-exact."""
    rng = np.random.default_rng(11)
    xyz = rng.uniform(0.0, 1.1, size=(10_000, 3))
    np.testing.assert_allclose(oklab_to_xyz(xyz_to_oklab(xyz)), xyz, atol=1e-12)


def test_oklch_roundtrip():
    rng = np.random.default_rng(12)
    oklab = srgb_to_oklab(rng.integers(0, 256, size=(10_000, 3)).astype(np.float64))
    np.testing.assert_allclose(oklch_to_oklab(oklab_to_oklch(oklab)), oklab, atol=1e-12)


def test_oklch_hue_is_in_range_and_pinned_at_zero_chroma():
    oklch = oklab_to_oklch(np.array([[0.5, 0.1, -0.1], [0.5, 0.0, 0.0], [0.2, -0.05, 0.0]]))
    assert np.all(oklch[:, 2] >= 0.0) and np.all(oklch[:, 2] < 360.0)
    assert oklch[1, 2] == 0.0, "hue is undefined at C == 0; it must be pinned, not arbitrary"


def test_negative_lms_does_not_produce_nan():
    """XYZ outside the spectral locus drives LMS negative.

    The signed cube root keeps Oklab defined there. `** (1/3)` would return
    NaN and quietly poison any downstream mean or distance, which is exactly
    the class of failure this space is meant to avoid.
    """
    far_out = np.array([[-0.5, 1.2, 1.5], [1.5, -0.3, -0.2], [0.0, 0.0, -1.0]])
    oklab = xyz_to_oklab(far_out)
    assert np.all(np.isfinite(oklab))
    np.testing.assert_allclose(oklab_to_xyz(oklab), far_out, atol=1e-12)


def test_shapes_are_preserved_and_batching_matches_elementwise():
    rng = np.random.default_rng(13)
    batch = rng.integers(0, 256, size=(4, 7, 3)).astype(np.float64)
    batched = srgb_to_oklab(batch)
    assert batched.shape == (4, 7, 3)
    flat = np.stack([srgb_to_oklab(c) for c in batch.reshape(-1, 3)]).reshape(4, 7, 3)
    # Not atol=0.0: bit-identical output between the batched-shape and
    # elementwise paths isn't a guarantee NumPy/BLAS make, just what
    # happens to hold today for a contraction this small. A tight
    # tolerance still catches a real vectorization bug without pinning
    # the test to that implementation detail.
    np.testing.assert_allclose(batched, flat, atol=1e-15)


def test_delta_e_ok_is_a_metric():
    rng = np.random.default_rng(14)
    a, b, c = (
        srgb_to_oklab(rng.integers(0, 256, size=(500, 3)).astype(np.float64)) for _ in range(3)
    )
    np.testing.assert_allclose(delta_e_ok(a, a), 0.0, atol=0.0)
    np.testing.assert_allclose(delta_e_ok(a, b), delta_e_ok(b, a), atol=0.0)
    assert np.all(delta_e_ok(a, c) <= delta_e_ok(a, b) + delta_e_ok(b, c) + 1e-12)


def test_arithmetic_mean_minimizes_summed_squared_distance():
    """The property that makes plain k-means legitimate in Oklab.

    PLAN.md 3.2(b) rests on this: the centroid of a cluster is its
    arithmetic mean, exactly, so k-means' assignment/update loop keeps its
    convergence guarantee here in a way it does not for CIELAB + dE00.
    Checked numerically against perturbed candidates rather than asserted.
    """
    rng = np.random.default_rng(15)
    points = srgb_to_oklab(rng.integers(0, 256, size=(200, 3)).astype(np.float64))
    mean = points.mean(axis=0)
    best = np.sum(delta_e_ok(points, mean) ** 2)
    for _ in range(50):
        candidate = mean + rng.normal(scale=0.05, size=3)
        assert np.sum(delta_e_ok(points, candidate) ** 2) >= best
