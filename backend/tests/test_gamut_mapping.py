"""Out-of-gamut Lab colors must be gamut-mapped, not hard-clipped.

Hard-clipping each linear RGB channel independently shifts hue for
saturated out-of-gamut colors (PLAN.md 2.7); this is what issue #5 flagged.
The fix holds Oklch lightness and hue fixed and reduces chroma instead
(the CSS Color 4 algorithm, via coloraide). These tests check the actual
property that matters -- hue stays close to the original -- against an
independently computed hard-clip baseline, not against a hand-derived
expected RGB triple.
"""

from __future__ import annotations

import numpy as np
import pytest
from coloraide import Color

from app.color.srgb_lab import lab_to_srgb, lab_to_xyz, linear_to_srgb, xyz_to_linear


def _oklch_hue(lab):
    L, a, b = (float(v) for v in lab)
    # "lab-d65", not coloraide's plain "lab" (that one's white-pointed at
    # D50, this whole module is D65). Getting this wrong here would make
    # this helper self-consistently wrong in the same way a bug in
    # lab_to_srgb itself could be, and silently stop catching it.
    return Color("lab-d65", [L, a, b]).convert("oklch")["hue"]


def _hard_clip_reference(lab: np.ndarray) -> np.ndarray:
    """The old behavior, reimplemented independently for comparison."""
    linear = xyz_to_linear(lab_to_xyz(lab))
    srgb = linear_to_srgb(np.clip(linear, 0.0, 1.0))
    return np.clip(srgb, 0.0, 1.0) * 255.0


# A strongly saturated blue, chosen because it's in-gamut in Lab but its
# linear RGB is out of [0, 1] on more than one channel (confirmed by hand
# against coloraide directly before writing this test).
_OUT_OF_GAMUT_LAB = np.array([40.0, 40.0, -110.0])

# Three more out-of-gamut colors, deliberately spanning different hue
# regions and magnitudes. Added after a color-conformance review caught
# a D50/D65 white-point mix-up in the implementation that the single case
# above didn't expose clearly enough (it reduced drift either way, just
# not by nearly as much as a correct D65 mapping would); [25, 60, -90] in
# particular flips from "better than hard-clip" to worse under that bug,
# which is exactly why a single hand-picked fixture isn't enough here.
_OUT_OF_GAMUT_LAB_CASES = [
    _OUT_OF_GAMUT_LAB,
    np.array([25.0, 60.0, -90.0]),
    np.array([50.0, 90.0, -20.0]),
    np.array([65.0, -75.0, 55.0]),
]

# An ordinary in-gamut color (mid-grey-ish), for the "unaffected" check.
_IN_GAMUT_LAB = np.array([55.0, 12.0, -8.0])


@pytest.mark.parametrize("lab", _OUT_OF_GAMUT_LAB_CASES)
def test_out_of_gamut_color_is_detected_as_out_of_gamut(lab):
    linear = xyz_to_linear(lab_to_xyz(lab))
    assert np.any((linear < 0.0) | (linear > 1.0)), (
        "test fixture is supposed to be out of the sRGB gamut, adjust it if this fails"
    )


@pytest.mark.parametrize("lab", _OUT_OF_GAMUT_LAB_CASES)
def test_gamut_mapped_hue_beats_hard_clip_hue(lab):
    original_hue = _oklch_hue(lab)

    hard_clipped_rgb = _hard_clip_reference(lab)
    hard_clipped_lab = Color("srgb", (hard_clipped_rgb / 255.0).tolist()).convert("lab-d65")
    hard_clip_hue = _oklch_hue(
        [hard_clipped_lab["lightness"], hard_clipped_lab["a"], hard_clipped_lab["b"]]
    )

    mapped_rgb = lab_to_srgb(lab)
    mapped_lab = Color("srgb", (mapped_rgb / 255.0).tolist()).convert("lab-d65")
    mapped_hue = _oklch_hue([mapped_lab["lightness"], mapped_lab["a"], mapped_lab["b"]])

    hard_clip_drift = abs(hard_clip_hue - original_hue)
    mapped_drift = abs(mapped_hue - original_hue)

    assert mapped_drift < hard_clip_drift, (
        f"gamut mapping should drift hue less than hard clipping: "
        f"mapped drift {mapped_drift:.2f} deg, hard-clip drift {hard_clip_drift:.2f} deg"
    )


@pytest.mark.parametrize("lab", _OUT_OF_GAMUT_LAB_CASES)
def test_gamut_mapped_output_is_in_gamut(lab):
    mapped_rgb = lab_to_srgb(lab)
    assert mapped_rgb.shape == (3,)
    assert np.all(mapped_rgb >= 0.0) and np.all(mapped_rgb <= 255.0)


def test_in_gamut_colors_are_unaffected():
    """The common case shouldn't change: no coloraide involvement, same
    exact matrix pipeline as before, still matches the hard-clip result
    because there's nothing to clip.
    """
    mapped = lab_to_srgb(_IN_GAMUT_LAB)
    reference = _hard_clip_reference(_IN_GAMUT_LAB)
    np.testing.assert_allclose(mapped, reference, atol=1e-8)


def test_batch_with_mixed_in_and_out_of_gamut_colors():
    batch = np.stack([_IN_GAMUT_LAB, _OUT_OF_GAMUT_LAB, _IN_GAMUT_LAB])
    result = lab_to_srgb(batch)
    assert result.shape == (3, 3)
    np.testing.assert_allclose(result[0], result[2])  # same input, same output
    assert np.all(result >= 0.0) and np.all(result <= 255.0)
