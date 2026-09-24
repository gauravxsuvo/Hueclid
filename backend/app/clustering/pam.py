"""Weighted k-medoids (FastPAM1 swap search) on a dissimilarity matrix.

PLAN.md 2.4a: restricting cluster centers to actual data points makes the
update step a finite search, so the objective decreases monotonically for
*any* dissimilarity -- including dE00, which is not a metric.

The `kmedoids` package (FasterPAM, Schubert & Rousseeuw 2021) has no sample
weights, and the Lab histogram bins are weighted by pixel count, so this
module implements the weighted variant directly: same objective, same
swap-neighbourhood, same O(k) per-candidate trick, evaluated for every
candidate at once with numpy. `kmedoids` is used in the tests as the
independent reference (uniform weights, and integer weights vs. duplicated
points).

Objective minimized: sum_i w_i * D[i, nearest medoid of i].
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from app.color.deltae2000 import delta_e2000_matrix


@dataclass
class PAMResult:
    medoids: np.ndarray  # (k,) row indices into the input points
    labels: np.ndarray  # (n,) index into `medoids` for each point
    objective: float
    n_iter: int  # swap-search passes, including the final non-improving one
    n_swaps: int
    converged: bool  # False only if max_iter was hit
    objective_history: list[float] = field(default_factory=list)  # BUILD, then per swap
    runtime_s: float = 0.0


def weighted_objective(diss: np.ndarray, weights: np.ndarray, medoids: np.ndarray) -> float:
    return float(np.dot(weights, diss[:, medoids].min(axis=1)))


def _validate(diss: np.ndarray, weights: np.ndarray, k: int) -> None:
    n = diss.shape[0]
    if diss.ndim != 2 or diss.shape[1] != n:
        raise ValueError("diss must be a square (n, n) matrix")
    if weights.shape != (n,):
        raise ValueError("weights must have shape (n,)")
    if np.any(weights <= 0):
        raise ValueError("weights must be strictly positive")
    if not 1 <= k <= n:
        raise ValueError(f"k must be in [1, n={n}], got {k}")


def weighted_build(diss: np.ndarray, weights: np.ndarray, k: int) -> np.ndarray:
    """PAM BUILD: greedily add the point that most reduces the weighted objective."""
    first = int(np.argmin(weights @ diss))
    medoids = [first]
    nearest = diss[:, first].copy()

    for _ in range(1, k):
        # gain[c] = sum_i w_i * max(nearest_i - D[i, c], 0)
        gain = weights @ np.maximum(nearest[:, None] - diss, 0.0)
        gain[medoids] = -np.inf
        c = int(np.argmax(gain))
        medoids.append(c)
        nearest = np.minimum(nearest, diss[:, c])

    return np.array(medoids, dtype=np.int64)


def _nearest_two(dm: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """dm (n, k) -> nearest index, nearest dissim, second-nearest dissim."""
    n, k = dm.shape
    rows = np.arange(n)
    nearest = np.argmin(dm, axis=1)
    dn = dm[rows, nearest]
    if k == 1:
        return nearest, dn, np.full(n, np.inf)
    masked = dm.copy()
    masked[rows, nearest] = np.inf
    return nearest, dn, masked.min(axis=1)


def _best_swap(
    diss: np.ndarray, weights: np.ndarray, medoids: np.ndarray
) -> tuple[float, int, int]:
    """Best (delta objective, medoid slot to drop, candidate point to add), over
    every (slot, candidate) pair -- FastPAM1's O(k)-per-candidate evaluation.

    For a candidate c replacing the medoid in slot m, a point i:
      - outside m's cluster keeps its medoid unless c is nearer: min(D_ic - dn_i, 0)
      - inside m's cluster falls back to min(second_i, D_ic)
    The first term is shared by every slot, so only the in-cluster correction
    is computed per slot.
    """
    dm = diss[:, medoids]
    nearest, dn, ds = _nearest_two(dm)

    gain_if_added = np.minimum(diss - dn[:, None], 0.0)  # (n, n): D[i, c] vs current nearest
    shared = weights @ gain_if_added  # (n,) over candidates c

    delta = np.empty((len(medoids), diss.shape[0]))
    for slot in range(len(medoids)):
        rows = np.flatnonzero(nearest == slot)
        if rows.size == 0:
            delta[slot] = shared
            continue
        d_rows = diss[rows]
        fallback = np.minimum(ds[rows, None], d_rows) - dn[rows, None] - gain_if_added[rows]
        delta[slot] = shared + weights[rows] @ fallback

    delta[:, medoids] = np.inf  # a current medoid is not a swap candidate
    flat = int(np.argmin(delta))
    slot, cand = divmod(flat, delta.shape[1])
    return float(delta[slot, cand]), slot, cand


def weighted_fastpam(
    diss: np.ndarray,
    weights: np.ndarray,
    k: int,
    init: str | np.ndarray = "build",
    max_iter: int = 100,
    rtol: float = 1e-12,
    random_state: int | None = None,
) -> PAMResult:
    """Weighted k-medoids by steepest-descent swaps from a BUILD (or given) start.

    Terminates at a swap-local-minimum: no single (medoid, non-medoid)
    exchange lowers the weighted objective. `init` is "build", "random", or
    an explicit array of k point indices.
    """
    t0 = time.perf_counter()
    diss = np.asarray(diss, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    _validate(diss, weights, k)

    if isinstance(init, str):
        if init == "build":
            medoids = weighted_build(diss, weights, k)
        elif init == "random":
            rng = np.random.default_rng(random_state)
            medoids = rng.choice(diss.shape[0], size=k, replace=False).astype(np.int64)
        else:
            raise ValueError(f"unknown init {init!r}")
    else:
        medoids = np.array(init, dtype=np.int64)
        if medoids.shape != (k,) or len(set(medoids.tolist())) != k:
            raise ValueError("init must be k distinct point indices")

    objective = weighted_objective(diss, weights, medoids)
    history = [objective]
    n_swaps = 0
    n_iter = 0
    converged = False

    while n_iter < max_iter:
        n_iter += 1
        if k == diss.shape[0]:
            converged = True
            break
        delta, slot, cand = _best_swap(diss, weights, medoids)
        if delta >= -rtol * max(objective, 1.0):
            converged = True
            break
        medoids[slot] = cand
        objective = weighted_objective(diss, weights, medoids)
        history.append(objective)
        n_swaps += 1

    labels = np.argmin(diss[:, medoids], axis=1)
    return PAMResult(
        medoids=medoids,
        labels=labels,
        objective=objective,
        n_iter=n_iter,
        n_swaps=n_swaps,
        converged=converged,
        objective_history=history,
        runtime_s=time.perf_counter() - t0,
    )


def cluster_lab_medoids_de00(
    lab_points: np.ndarray,
    weights: np.ndarray,
    k: int,
    power: float = 2.0,
    **kwargs,
) -> PAMResult:
    """Weighted k-medoids over Lab points under dE00**power.

    power=2 makes the objective the dE00 analogue of k-means' within-cluster
    sum of squares (and matches the drift term in PLAN.md 2.6c); power=1 is
    classic PAM's sum of distances.
    """
    lab_points = np.asarray(lab_points, dtype=np.float64)
    diss = delta_e2000_matrix(lab_points, lab_points)
    np.fill_diagonal(diss, 0.0)  # exact zero; the formula can leave ~1e-8 of float noise
    if power != 1.0:
        diss = diss**power
    return weighted_fastpam(diss, weights, k, **kwargs)
