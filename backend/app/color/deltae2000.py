"""CIEDE2000 (dE00) color difference, vectorized.

Reference: PLAN.md section 2.3; Sharma, Wu & Dalal (2005). This is a
dissimilarity, not a metric (violates the triangle inequality via the
R_T rotation term) -- do not assume it behaves like Euclidean distance.
"""
from __future__ import annotations

import numpy as np


def delta_e2000(
    lab1: np.ndarray,
    lab2: np.ndarray,
    kL: float = 1.0,
    kC: float = 1.0,
    kH: float = 1.0,
) -> np.ndarray:
    """CIEDE2000 between every pair in lab1 (n,3) and lab2 (k,3) -> (n,k).

    Also accepts equal-shape (...,3) arrays for elementwise comparison
    (broadcast (n,3) vs (n,3) -> (n,)) when lab1.shape == lab2.shape and
    a pairwise matrix isn't wanted -- see `delta_e2000_pairwise` below for
    the always-broadcasting form used by clustering.
    """
    lab1 = np.asarray(lab1, dtype=np.float64)
    lab2 = np.asarray(lab2, dtype=np.float64)

    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    Cbar = (C1 + C2) / 2.0
    G = 0.5 * (1.0 - np.sqrt(Cbar**7 / (Cbar**7 + 25.0**7)))

    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = np.sqrt(a1p**2 + b1**2)
    C2p = np.sqrt(a2p**2 + b2**2)

    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0
    # atan2(0, 0) is defined as 0 by numpy already, matching the spec.

    dLp = L2 - L1
    dCp = C2p - C1p

    dhp_raw = h2p - h1p
    dhp = np.where(
        np.abs(dhp_raw) <= 180.0,
        dhp_raw,
        np.where(dhp_raw > 180.0, dhp_raw - 360.0, dhp_raw + 360.0),
    )
    dhp = np.where(C1p * C2p == 0.0, 0.0, dhp)

    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2.0))

    Lbp = (L1 + L2) / 2.0
    Cbp = (C1p + C2p) / 2.0

    hsum = h1p + h2p
    habs = np.abs(h1p - h2p)
    hbp = np.where(
        habs <= 180.0,
        hsum / 2.0,
        np.where(hsum < 360.0, (hsum + 360.0) / 2.0, (hsum - 360.0) / 2.0),
    )
    hbp = np.where(C1p * C2p == 0.0, hsum, hbp)

    T = (
        1.0
        - 0.17 * np.cos(np.radians(hbp - 30.0))
        + 0.24 * np.cos(np.radians(2.0 * hbp))
        + 0.32 * np.cos(np.radians(3.0 * hbp + 6.0))
        - 0.20 * np.cos(np.radians(4.0 * hbp - 63.0))
    )

    dTheta = 30.0 * np.exp(-(((hbp - 275.0) / 25.0) ** 2))
    R_C = 2.0 * np.sqrt(Cbp**7 / (Cbp**7 + 25.0**7))

    S_L = 1.0 + (0.015 * (Lbp - 50.0) ** 2) / np.sqrt(20.0 + (Lbp - 50.0) ** 2)
    S_C = 1.0 + 0.045 * Cbp
    S_H = 1.0 + 0.015 * Cbp * T
    R_T = -np.sin(np.radians(2.0 * dTheta)) * R_C

    termL = dLp / (kL * S_L)
    termC = dCp / (kC * S_C)
    termH = dHp / (kH * S_H)

    dE = np.sqrt(termL**2 + termC**2 + termH**2 + R_T * termC * termH)
    return dE


def delta_e2000_matrix(lab_a: np.ndarray, lab_b: np.ndarray) -> np.ndarray:
    """Pairwise CIEDE2000: lab_a (n,3), lab_b (k,3) -> (n,k) matrix.

    Broadcasts every (sin/cos/atan2) op over the full n*k grid in one
    shot -- do not loop over pixels/candidates (PLAN.md 2.3).
    """
    lab_a = np.asarray(lab_a, dtype=np.float64)[:, None, :]  # (n,1,3)
    lab_b = np.asarray(lab_b, dtype=np.float64)[None, :, :]  # (1,k,3)
    return delta_e2000(lab_a, lab_b)
