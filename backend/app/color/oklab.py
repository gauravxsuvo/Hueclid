"""CIE XYZ (D65) <-> Oklab <-> Oklch, vectorized over (..., 3) arrays.

Reference: PLAN.md section 2.2, and Bjorn Ottosson's original post,
https://bottosson.github.io/posts/oklab/ ("A perceptual color space for
image processing", 2020). Oklab is also normative in CSS Color 4.

Why this space exists alongside `srgb_lab`: CIELAB has a well-known hue
nonlinearity in the blue region, and -- more importantly for this project
-- CIELAB paired with dE00 is *not* a Euclidean metric space, so the
arithmetic mean is not the correct centroid and plain k-means has no
guarantees in it. Oklab is Euclidean by construction, so the mean is the
right minimizer and standard k-means applies with its guarantees intact.
PLAN.md 3.2(b) makes Oklab + Euclidean k-means a first-class arm of the
comparison, not a strawman, and that needs this module.

XYZ is the pivot, not linear sRGB. Ottosson publishes a direct
linear-sRGB -> Oklab matrix as a convenience (it's the one quoted in
PLAN.md 2.2), but it folds in his own rounding of the sRGB primaries,
which differs in the 7th decimal from the matrix `srgb_lab` already uses.
Going through XYZ keeps one set of primaries and one white point for the
whole codebase, so Lab and Oklab describe the same color rather than two
colors a hair apart. The direct matrix is still checked, as an
independently sourced reference implementation, in
`tests/test_oklab_conformance.py`.

Two deliberate departures from the constants as PLAN.md 2.2 quotes them,
both found by the conformance tests rather than assumed up front, and both
about keeping the *neutral axis exact* -- a grey must come out with
a == b == 0, not 1e-4 of a blue cast, because the whole point of adding a
second color space here is to compare it against CIELAB (PLAN.md 3.2b,
5.2). If Lab's neutral axis is exact and Oklab's is not, the color-space
ablation is measuring our arithmetic as much as the spaces:

1. The matrices below are CSS Color 4's, not the ones from Ottosson's
   2020 post. They are a later refinement of the same transform, and the
   difference is not rounding: Ottosson's published 10-digit M1 sends D65
   white to LMS (0.99989, 1.00003, 1.00048), off by 5e-4 in S, while the
   CSS matrices send it to exactly (1, 1, 1). The refined values are what
   CSS Color 4 made normative and what `coloraide` implements.
2. They are then von Kries-normalized to *this codebase's* D65
   (`srgb_lab._XN/_YN/_ZN` = 0.95047, 1, 1.08883, the ASTM E308 value that
   the sRGB->XYZ matrix in that module is built around). CSS Color 4
   instead derives D65 from the (0.3127, 0.3290) chromaticity, giving
   0.9504559, 1, 1.0890578 -- a real difference in the 5th decimal, and
   enough to leave greys slightly non-neutral if the two are mixed.
   Scaling the LMS rows so the working white maps to (1, 1, 1) is exactly
   the normalization that produced the published matrix in the first
   place, just re-applied to the white point actually in use here.

The net effect of (2) is a ~4e-5 disagreement with an unadapted
implementation such as coloraide, far below any perceptual threshold, in
exchange for an exactly neutral grey axis. `tests/test_oklab_conformance.py`
asserts both halves of that trade so neither can silently regress.

All functions accept and return float64 ndarrays of shape (..., 3).
"""

from __future__ import annotations

import numpy as np

from app.color.srgb_lab import (
    D65_WHITE_XYZ,
    linear_to_xyz,
    srgb_to_linear,
    xyz_to_srgb_gamut_mapped,
)

# M1: XYZ (D65) -> a cone-response-like LMS basis. CSS Color 4, section
# "Converting from XYZ to Oklab".
_CSS_XYZ_TO_LMS = np.array(
    [
        [0.8190224379967030, 0.3619062600528904, -0.1288737815209879],
        [0.0329836539323885, 0.9292868615863434, 0.0361446663506424],
        [0.0481771893596242, 0.2642395317527308, 0.6335478284694309],
    ],
    dtype=np.float64,
)

# M2: nonlinear (cube-rooted) LMS -> Oklab. Its rows sum to exactly
# (1, 0, 0), which is what makes LMS' == (1, 1, 1) come out as Oklab
# (1, 0, 0); that identity is why normalizing M1 below is sufficient.
_LMS_TO_OKLAB = np.array(
    [
        [0.2104542683093140, 0.7936177747023054, -0.0040720430116193],
        [1.9779985324311684, -2.4285922420485799, 0.4505937096174110],
        [0.0259040424655478, 0.7827717124575296, -0.8086757549230774],
    ],
    dtype=np.float64,
)

# von Kries normalization onto this codebase's white point: see (2) above.
_XYZ_TO_LMS = _CSS_XYZ_TO_LMS / (_CSS_XYZ_TO_LMS @ D65_WHITE_XYZ)[:, None]

# The inverses are published too, but inverting numerically means two
# fewer hand-transcribed 16-digit matrices to get wrong, and it makes the
# round-trip exact to float64 rather than to the published rounding.
_LMS_TO_XYZ = np.linalg.inv(_XYZ_TO_LMS)
_OKLAB_TO_LMS = np.linalg.inv(_LMS_TO_OKLAB)


def xyz_to_oklab(xyz: np.ndarray) -> np.ndarray:
    """CIE XYZ (D65) -> Oklab. L is in [0, 1], not [0, 100].

    Y is typically in [0, 1], but that is not an enforced precondition:
    the signed cube root below keeps this defined (and invertible) for
    Y outside that range and for XYZ with negative components, both of
    which the property tests in test_oklab_roundtrip.py exercise directly.
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    lms = xyz @ _XYZ_TO_LMS.T
    # np.cbrt, not `** (1/3)`: LMS can go slightly negative for colors
    # outside the spectral locus, and the signed cube root is what keeps
    # Oklab defined (and invertible) there instead of producing NaN.
    lms_ = np.cbrt(lms)
    return lms_ @ _LMS_TO_OKLAB.T


def oklab_to_xyz(oklab: np.ndarray) -> np.ndarray:
    oklab = np.asarray(oklab, dtype=np.float64)
    lms_ = oklab @ _OKLAB_TO_LMS.T
    lms = lms_**3
    return lms @ _LMS_TO_XYZ.T


def oklab_to_oklch(oklab: np.ndarray) -> np.ndarray:
    """Polar form: (L, C, h) with h in degrees, wrapped to [0, 360)."""
    oklab = np.asarray(oklab, dtype=np.float64)
    L, a, b = oklab[..., 0], oklab[..., 1], oklab[..., 2]
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360.0
    # Hue is meaningless at C == 0 and atan2 will happily return some
    # arbitrary angle there; pin it to 0 so achromatic colors compare equal.
    h = np.where(C == 0.0, 0.0, h)
    return np.stack([L, C, h], axis=-1)


def oklch_to_oklab(oklch: np.ndarray) -> np.ndarray:
    oklch = np.asarray(oklch, dtype=np.float64)
    L, C, h = oklch[..., 0], oklch[..., 1], oklch[..., 2]
    rad = np.radians(h)
    return np.stack([L, C * np.cos(rad), C * np.sin(rad)], axis=-1)


def srgb_to_oklab(srgb_255: np.ndarray) -> np.ndarray:
    """Convenience: uint8-range sRGB [0, 255] -> Oklab."""
    srgb = np.asarray(srgb_255, dtype=np.float64) / 255.0
    return xyz_to_oklab(linear_to_xyz(srgb_to_linear(srgb)))


def oklab_to_srgb(oklab: np.ndarray) -> np.ndarray:
    """Oklab -> uint8-range sRGB [0, 255], gamut-mapped, not hard-clipped.

    Shares the exact gamut-mapping tail `lab_to_srgb` uses, for the reason
    given in that function's docstring: out-of-gamut colors get their Oklch
    chroma reduced with lightness and hue held fixed.
    """
    return xyz_to_srgb_gamut_mapped(oklab_to_xyz(oklab))


def delta_e_ok(oklab1: np.ndarray, oklab2: np.ndarray) -> np.ndarray:
    """Euclidean distance in Oklab.

    Deliberately a plain L2 norm and nothing more. That is the whole point
    of the space: unlike CIELAB, where a perceptual distance needs dE00's
    correction terms, Oklab is built so that Euclidean distance already is
    the perceptual distance. Named to sit next to `delta_e2000` so the two
    are interchangeable wherever a distance metric is a parameter.
    """
    a = np.asarray(oklab1, dtype=np.float64)
    b = np.asarray(oklab2, dtype=np.float64)
    return np.linalg.norm(a - b, axis=-1)
