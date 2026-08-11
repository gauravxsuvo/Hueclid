"""Oklab conformance: Ottosson's published reference values and matrices.

PLAN.md 2.2 quotes the Oklab matrices from memory and warns, in the
document itself, that a transposed digit would silently poison every
downstream number. So none of the constants in `app.color.oklab` are
trusted on the strength of that quote. They are checked here three ways,
against sources that were derived independently of each other:

1. The XYZ -> Oklab reference table published in Ottosson's original post
   (https://bottosson.github.io/posts/oklab/, section "Table of example
   XYZ and Oklab pairs"). This is the primary check: it pins the actual
   numeric output of the transform, not just the matrix entries.
2. Ottosson's separately published linear-sRGB -> Oklab matrix, typed out
   below as a standalone reference implementation. It is a different
   derivation of the same transform (he folded the sRGB primaries into
   M1 himself), so agreement to within the primaries' rounding is
   meaningful evidence and disagreement in any earlier digit is not.
3. coloraide's "oklab" space, a third-party implementation maintained
   against the CSS Color 4 spec.

The ~1e-4 tolerances on checks 2 and 3 are not slack for sloppiness. They
are the known, quantified disagreement between three things that are all
correct but not identical: Ottosson's original matrices, CSS Color 4's
refinement of them, and which numeric D65 each is normalized to (see the
module docstring in app/color/oklab.py). A real transcription error in
any of the 18 matrix entries moves the result by orders of magnitude
more than this, so the tolerance still catches what it is here to catch.

The neutral-axis tests at the bottom are the ones that fail if the white
points get mixed up, and they are exact rather than approximate on
purpose -- they are the reason this module adapts the matrices at all.
"""

from __future__ import annotations

import numpy as np
import pytest
from coloraide import Color

from app.color.oklab import oklab_to_oklch, srgb_to_oklab, xyz_to_oklab
from app.color.srgb_lab import D65_WHITE_XYZ, srgb_to_lab, srgb_to_linear

# --- 1. Ottosson's XYZ -> Oklab table -------------------------------------
#
# Quoted to the three decimals the post gives, for both input and output.
# Because the *inputs* are rounded too (0.950 is not exactly D65's 0.95047),
# the achievable agreement is bounded by that rounding, not by our precision;
# 5e-4 is the tightest tolerance that a correctly rounded 3-decimal table
# can be held to.
OTTOSSON_XYZ_OKLAB = [
    ((0.950, 1.000, 1.089), (1.000, 0.000, 0.000)),  # D65 white
    ((1.000, 0.000, 0.000), (0.450, 1.236, -0.019)),
    ((0.000, 1.000, 0.000), (0.922, -0.671, 0.263)),
    ((0.000, 0.000, 1.000), (0.153, -1.415, -0.449)),
]


@pytest.mark.parametrize("xyz,expected", OTTOSSON_XYZ_OKLAB)
def test_ottosson_reference_table(xyz, expected):
    got = xyz_to_oklab(np.array(xyz, dtype=np.float64))
    np.testing.assert_allclose(got, expected, atol=5e-4)


# --- 2. Ottosson's direct linear-sRGB -> Oklab matrix ---------------------

_OTTOSSON_LINEAR_SRGB_TO_LMS = np.array(
    [
        [0.4122214708, 0.5363325363, 0.0514459929],
        [0.2119034982, 0.6806995451, 0.1073969566],
        [0.0883024619, 0.2817188376, 0.6299787005],
    ],
    dtype=np.float64,
)
_OTTOSSON_LMS_TO_OKLAB = np.array(
    [
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660],
    ],
    dtype=np.float64,
)


def _ottosson_reference_srgb_to_oklab(srgb_255: np.ndarray) -> np.ndarray:
    """Ottosson's sRGB path, standalone: no imports from app.color.oklab."""
    linear = srgb_to_linear(np.asarray(srgb_255, dtype=np.float64) / 255.0)
    lms_ = np.cbrt(linear @ _OTTOSSON_LINEAR_SRGB_TO_LMS.T)
    return lms_ @ _OTTOSSON_LMS_TO_OKLAB.T


def test_matches_ottosson_direct_srgb_matrix():
    rng = np.random.default_rng(20200101)
    rgb = rng.integers(0, 256, size=(5000, 3)).astype(np.float64)
    max_diff = np.max(np.abs(srgb_to_oklab(rgb) - _ottosson_reference_srgb_to_oklab(rgb)))
    assert max_diff < 1e-4, f"max |Oklab difference| vs Ottosson's sRGB matrix = {max_diff}"


def test_srgb_primary_corners_match_ottosson_direct_matrix():
    """The eight RGB cube corners, where any matrix-entry error is loudest."""
    corners = np.array(
        [[r, g, b] for r in (0.0, 255.0) for g in (0.0, 255.0) for b in (0.0, 255.0)]
    )
    np.testing.assert_allclose(
        srgb_to_oklab(corners), _ottosson_reference_srgb_to_oklab(corners), atol=1e-4
    )


# --- 3. coloraide, a third-party implementation ---------------------------


def test_matches_coloraide_oklab():
    rng = np.random.default_rng(7)
    rgb = rng.integers(0, 256, size=(400, 3)).astype(np.float64)
    reference = np.array([Color("srgb", list(c / 255.0)).convert("oklab")[:-1] for c in rgb])
    max_diff = np.max(np.abs(srgb_to_oklab(rgb) - reference))
    assert max_diff < 1e-4, f"max |Oklab difference| vs coloraide = {max_diff}"


def test_matches_coloraide_oklch():
    rng = np.random.default_rng(8)
    rgb = rng.integers(0, 256, size=(200, 3)).astype(np.float64)
    got = oklab_to_oklch(srgb_to_oklab(rgb))
    for i, c in enumerate(rgb):
        ref = Color("srgb", list(c / 255.0)).convert("oklch")
        assert abs(got[i, 0] - ref["lightness"]) < 1e-4
        assert abs(got[i, 1] - ref["chroma"]) < 1e-4
        ref_hue = ref["hue"]
        if np.isnan(ref_hue) or got[i, 1] < 1e-3:
            # Hue is meaningless near the neutral axis: a 4e-5 difference in
            # (a, b) between two implementations swings it by tens of
            # degrees while the colors stay visually identical. Chroma,
            # asserted above, is the meaningful check down here.
            continue
        # Compare on the circle, so 359.99 and 0.01 are close, not 360 apart.
        hue_diff = abs((got[i, 2] - ref_hue + 180.0) % 360.0 - 180.0)
        assert hue_diff < 0.05, f"hue {got[i, 2]} vs {ref_hue} for rgb {c}"


# --- The neutral axis: exact, and independent of any reference impl -------


def test_the_working_white_point_maps_to_oklab_exactly():
    """D65 -> (1, 0, 0) to the last float64 bit, by construction.

    This is what the von Kries normalization in app/color/oklab.py buys.
    Without it the same input comes out ~9e-5 off in b, because the
    codebase's ASTM D65 gets read through matrices normalized to CSS
    Color 4's slightly different D65. Asserted at the XYZ pivot rather
    than from sRGB because this is the only point in the chain where the
    claim is exact -- see the next test for why.
    """
    np.testing.assert_allclose(xyz_to_oklab(D65_WHITE_XYZ), [1.0, 0.0, 0.0], atol=1e-15)


def test_black_is_the_origin():
    np.testing.assert_allclose(
        srgb_to_oklab(np.array([0.0, 0.0, 0.0])), [0.0, 0.0, 0.0], atol=1e-12
    )


# Everything reached through `srgb_to_lab`/`srgb_to_oklab` inherits one
# more error term that has nothing to do with Oklab: `_SRGB_TO_XYZ` is the
# standard 7-digit sRGB primaries matrix, and its middle row sums to
# 1.0000001 rather than 1, so sRGB white lands a hair off the declared D65
# before either space sees it. That is a property of Phase 0's matrix,
# it applies identically to the CIELAB path (Lab white is 100.00000004,
# -1.7e-5, 6.7e-6), and it bounds how neutral any grey can be here.
_SRGB_MATRIX_ROUNDING = 1e-7


def test_neutral_greys_are_achromatic_and_monotonic_in_lightness():
    """Every grey, not just white: the whole neutral axis must be neutral.

    Downstream this is load-bearing. Backgrounds and surfaces in the role
    graph (PLAN.md 6) are near-neutral by construction, and a chroma floor
    smeared across them would make "is this color neutral" a threshold
    question instead of essentially an exact one.
    """
    greys = np.stack([np.arange(0, 256, 5.0)] * 3, axis=-1)
    oklab = srgb_to_oklab(greys)
    assert np.max(np.abs(oklab[:, 1:])) < _SRGB_MATRIX_ROUNDING, (
        "a grey ramp must be achromatic to within the sRGB matrix's own rounding"
    )
    assert np.all(np.diff(oklab[:, 0]) > 0), "L must increase monotonically along a grey ramp"


def test_white_point_agrees_with_the_cielab_module():
    """The two spaces must call the same color white, or the color-space
    ablation (PLAN.md 5.2) measures our arithmetic as well as the spaces.

    Neither space adds error of its own here; both just inherit the sRGB
    matrix rounding above. Lab gets a looser bound only because its a/b
    formulas carry gains of 500 and 200 against Oklab's order-of-1
    coefficients, so the identical input error surfaces a few times
    larger once both are put on a common 0-1 lightness scale.
    """
    white = np.array([255.0, 255.0, 255.0])
    lab_white = srgb_to_lab(white) / 100.0
    oklab_white = srgb_to_oklab(white)
    np.testing.assert_allclose(lab_white[1:], [0.0, 0.0], atol=5 * _SRGB_MATRIX_ROUNDING)
    np.testing.assert_allclose(oklab_white[1:], [0.0, 0.0], atol=_SRGB_MATRIX_ROUNDING)
    np.testing.assert_allclose(lab_white[0], oklab_white[0], atol=_SRGB_MATRIX_ROUNDING)
