"""Property tests: sRGB -> Lab -> sRGB round-trips to within float tolerance.

PLAN.md 9.1: round-trip 10,000 random sRGB triples, max dE00 < 1e-6.
"""
from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from app.color.deltae2000 import delta_e2000
from app.color.srgb_lab import lab_to_srgb, srgb_to_lab

rgb_byte = st.integers(min_value=0, max_value=255)


@settings(max_examples=1000, deadline=None)
@given(r=rgb_byte, g=rgb_byte, b=rgb_byte)
def test_roundtrip_single_pixel(r, g, b):
    original = np.array([r, g, b], dtype=np.float64)
    lab = srgb_to_lab(original)
    recovered = lab_to_srgb(lab)
    assert np.max(np.abs(recovered - original)) < 0.01


def test_roundtrip_batch_10000_max_deltae():
    rng = np.random.default_rng(42)
    original = rng.integers(0, 256, size=(10_000, 3)).astype(np.float64)
    lab = srgb_to_lab(original)
    recovered_rgb = lab_to_srgb(lab)
    recovered_lab = srgb_to_lab(recovered_rgb)
    max_de = np.max(delta_e2000(lab, recovered_lab))
    assert max_de < 1e-6, f"max dE00 round-trip error = {max_de}"


def test_known_reference_points():
    """A few colors with well-known Lab values (D65), sanity-checked by hand."""
    # Pure white
    lab_white = srgb_to_lab(np.array([255.0, 255.0, 255.0]))
    np.testing.assert_allclose(lab_white, [100.0, 0.0, 0.0], atol=0.01)

    # Pure black
    lab_black = srgb_to_lab(np.array([0.0, 0.0, 0.0]))
    np.testing.assert_allclose(lab_black, [0.0, 0.0, 0.0], atol=0.01)


def test_srgb_linear_roundtrip_vectorized():
    from app.color.srgb_lab import linear_to_srgb, srgb_to_linear

    x = np.linspace(0, 1, 2049)
    np.testing.assert_allclose(linear_to_srgb(srgb_to_linear(x)), x, atol=1e-10)
