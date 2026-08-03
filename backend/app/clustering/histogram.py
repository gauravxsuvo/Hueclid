"""Sparse Lab-space histogram binning (PLAN.md section 2.4a: 'bin, don't sample').

Every pixel votes into exactly one bin; the bin's representative point is
the mean Lab position of the pixels that landed in it (not the bin's grid
center), so quantization error stays well under 1 dE00 at a 2-unit grid.
"""
from __future__ import annotations

import numpy as np


def build_lab_histogram(
    lab_pixels: np.ndarray,
    l_step: float = 2.0,
    a_step: float = 2.0,
    b_step: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """lab_pixels: (N, 3) -> (bin_points (M, 3), weights (M,) int counts)."""
    lab_pixels = np.asarray(lab_pixels, dtype=np.float64).reshape(-1, 3)
    steps = np.array([l_step, a_step, b_step], dtype=np.float64)

    idx = np.floor(lab_pixels / steps).astype(np.int64)
    unique_idx, inverse, counts = np.unique(idx, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.reshape(-1)

    sums = np.zeros((unique_idx.shape[0], 3), dtype=np.float64)
    np.add.at(sums, inverse, lab_pixels)
    bin_points = sums / counts[:, None]

    return bin_points, counts
