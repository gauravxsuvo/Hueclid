"""sRGB <-> linear RGB <-> CIE XYZ <-> CIELAB, vectorized over (..., 3) arrays.

Reference: PLAN.md section 2.1. D65 white point, sRGB primaries.
All functions accept and return float64 ndarrays of shape (..., 3).
"""

from __future__ import annotations

import numpy as np
from coloraide import Color

# sRGB primaries -> XYZ (D65), and its inverse.
_SRGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=np.float64,
)
_XYZ_TO_SRGB = np.linalg.inv(_SRGB_TO_XYZ)

# D65 reference white. The ASTM E308 value, which is the one the sRGB
# matrix above is built around -- its rows sum to this (up to the
# matrix's own 7-digit rounding, ~1e-7), so sRGB white lands within that
# rounding of Lab (100, 0, 0). Note this is NOT the value CSS Color 4
# uses (0.9504559, 1, 1.0890578, derived from the (0.3127, 0.3290)
# chromaticity); they differ in the 5th decimal. Both are in wide use, but
# mixing them within one pipeline puts a small cast on the neutral axis,
# so this is the single definition every color space in this package
# adapts to. See app/color/oklab.py for where that matters.
_XN, _YN, _ZN = 0.95047, 1.00000, 1.08883
D65_WHITE_XYZ = np.array([_XN, _YN, _ZN], dtype=np.float64)

_LAB_EPS = 216.0 / 24389.0  # 0.008856...
_LAB_KAPPA = 24389.0 / 27.0  # 903.296...


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """Undo the sRGB EOTF. Input in [0, 1]."""
    srgb = np.asarray(srgb, dtype=np.float64)
    linear = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )
    return linear


def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Apply the sRGB EOTF (encode). Input in [0, 1] linear light."""
    linear = np.asarray(linear, dtype=np.float64)
    linear = np.clip(linear, 0.0, None)
    srgb = np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * (linear ** (1.0 / 2.4)) - 0.055,
    )
    return srgb


def linear_to_xyz(linear: np.ndarray) -> np.ndarray:
    linear = np.asarray(linear, dtype=np.float64)
    return linear @ _SRGB_TO_XYZ.T


def xyz_to_linear(xyz: np.ndarray) -> np.ndarray:
    xyz = np.asarray(xyz, dtype=np.float64)
    return xyz @ _XYZ_TO_SRGB.T


def _f(t: np.ndarray) -> np.ndarray:
    return np.where(t > _LAB_EPS, np.cbrt(t), (_LAB_KAPPA * t + 16.0) / 116.0)


def _f_inv(t: np.ndarray) -> np.ndarray:
    t3 = t**3
    return np.where(t3 > _LAB_EPS, t3, (116.0 * t - 16.0) / _LAB_KAPPA)


def xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    xyz = np.asarray(xyz, dtype=np.float64)
    fx = _f(xyz[..., 0] / _XN)
    fy = _f(xyz[..., 1] / _YN)
    fz = _f(xyz[..., 2] / _ZN)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def lab_to_xyz(lab: np.ndarray) -> np.ndarray:
    lab = np.asarray(lab, dtype=np.float64)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    x = _f_inv(fx) * _XN
    y = _f_inv(fy) * _YN
    z = _f_inv(fz) * _ZN
    return np.stack([x, y, z], axis=-1)


def srgb_to_lab(srgb_255: np.ndarray) -> np.ndarray:
    """Convenience: uint8-range sRGB [0, 255] -> CIELAB."""
    srgb = np.asarray(srgb_255, dtype=np.float64) / 255.0
    return xyz_to_lab(linear_to_xyz(srgb_to_linear(srgb)))


def xyz_to_srgb_gamut_mapped(xyz: np.ndarray) -> np.ndarray:
    """CIE XYZ (D65) -> uint8-range sRGB [0, 255], gamut-mapped.

    In-gamut colors go through the matrix pipeline above (exact, and
    covered by the round-trip conformance tests). Colors that fall outside
    the sRGB gamut are gamut-mapped instead of hard-clipped: hard clipping
    shifts hue, sometimes badly, because clipping each channel independently
    doesn't hold hue or lightness fixed. The CSS Color 4 algorithm holds
    Oklch lightness and hue fixed and reduces chroma until the color lands
    back in gamut; `fit(method="oklch-chroma")` implements exactly that,
    so it's used here rather than a hand-rolled version (see PLAN.md 2.7).
    Not coloraide's own default `fit()` method, hence passing it explicitly.

    Takes XYZ rather than (L, a, b) so that every color space in this
    package shares one gamut-mapping implementation, and so that coloraide
    is handed coordinates in a space whose white point is unambiguous.
    coloraide's plain "lab" space is the CSS-spec space, white-pointed at
    D50, while this package is D65 throughout -- passing D65 coordinates
    into "lab" silently reinterprets them as D50, a wrong starting color,
    not just a rounding error, caught by color-conformance review before
    this shipped. Going through this package's own XYZ instead of even
    coloraide's own (correct) "lab-d65" space avoids relying on two
    independently-computed conversions agreeing with each other.
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    linear = xyz_to_linear(xyz)
    # A tolerance, not an exact 0/1 boundary: colors that are in gamut but
    # land a float64 epsilon past 0 or 1 after the matrix/cbrt chain above
    # must not get routed through gamut mapping, that's a bug, not a fix
    # (it did happen during development -- a color with linear ~= -1.8e-18
    # tripped the strict check and came back visibly wrong).
    _GAMUT_TOL = 1e-6
    out_of_gamut = np.any((linear < -_GAMUT_TOL) | (linear > 1.0 + _GAMUT_TOL), axis=-1)

    srgb = linear_to_srgb(np.clip(linear, 0.0, 1.0))

    if np.any(out_of_gamut):
        flat_xyz = xyz.reshape(-1, 3)
        flat_srgb = srgb.reshape(-1, 3)
        for i in np.flatnonzero(out_of_gamut.reshape(-1)):
            mapped = Color("xyz-d65", list(flat_xyz[i])).convert("srgb").fit(method="oklch-chroma")
            flat_srgb[i] = mapped[:-1]
        srgb = flat_srgb.reshape(srgb.shape)

    return np.clip(srgb, 0.0, 1.0) * 255.0


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """CIELAB -> uint8-range sRGB [0, 255], gamut-mapped, not hard-clipped.

    See `xyz_to_srgb_gamut_mapped` for what happens to out-of-gamut colors.
    """
    lab = np.asarray(lab, dtype=np.float64)
    return xyz_to_srgb_gamut_mapped(lab_to_xyz(lab))
