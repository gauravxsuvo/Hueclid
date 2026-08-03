"""sRGB <-> linear RGB <-> CIE XYZ <-> CIELAB, vectorized over (..., 3) arrays.

Reference: PLAN.md section 2.1. D65 white point, sRGB primaries.
All functions accept and return float64 ndarrays of shape (..., 3).
"""
from __future__ import annotations

import numpy as np

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

# D65 reference white.
_XN, _YN, _ZN = 0.95047, 1.00000, 1.08883

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


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """CIELAB -> uint8-range sRGB [0, 255], hard-clipped to gamut.

    NOTE: hard clipping shifts hue for out-of-gamut colors (PLAN.md 2.7).
    This is a placeholder for the vertical slice; replace with Oklch
    chroma-bisection gamut mapping before shipping the constrained
    palette synthesis stage.
    """
    linear = xyz_to_linear(lab_to_xyz(lab))
    srgb = linear_to_srgb(np.clip(linear, 0.0, 1.0))
    return np.clip(srgb * 255.0, 0.0, 255.0)
