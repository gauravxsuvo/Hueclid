"""Weighted FastPAM: correctness properties, and agreement with the `kmedoids`
package (the independent reference) where that package can express the problem.

`kmedoids` has no sample weights, so the two comparisons are:
  - uniform weights: same problem, compare objectives directly
  - integer weights: equivalent to duplicating each point w_i times, which
    `kmedoids` can run
"""

from __future__ import annotations

import itertools

import kmedoids
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.clustering.pam import (
    cluster_lab_medoids_de00,
    weighted_build,
    weighted_fastpam,
    weighted_objective,
)
from app.color.deltae2000 import delta_e2000_matrix


def _euclid(points: np.ndarray) -> np.ndarray:
    d = points[:, None, :] - points[None, :, :]
    return np.sqrt((d**2).sum(-1))


def _blobs(rng, centers, per_blob, spread=1.0):
    pts = np.concatenate([c + rng.normal(0, spread, (per_blob, len(c))) for c in centers])
    return pts


def _is_swap_local_min(diss, weights, medoids, tol=1e-9) -> bool:
    base = weighted_objective(diss, weights, medoids)
    n = diss.shape[0]
    for slot in range(len(medoids)):
        for c in range(n):
            if c in medoids:
                continue
            trial = medoids.copy()
            trial[slot] = c
            if weighted_objective(diss, weights, trial) < base - tol * max(base, 1.0):
                return False
    return True


def _brute_force_optimum(diss, weights, k) -> float:
    n = diss.shape[0]
    return min(
        weighted_objective(diss, weights, np.array(combo))
        for combo in itertools.combinations(range(n), k)
    )


@given(
    seed=st.integers(0, 10_000),
    n=st.integers(5, 40),
    k=st.integers(1, 5),
)
@settings(max_examples=60, deadline=None)
def test_terminates_at_swap_local_minimum_with_monotone_descent(seed, n, k):
    rng = np.random.default_rng(seed)
    pts = rng.normal(size=(n, 3)) * 10
    weights = rng.integers(1, 1000, size=n).astype(float)
    diss = _euclid(pts)

    res = weighted_fastpam(diss, weights, k, init="random", random_state=seed)

    assert res.converged
    hist = np.array(res.objective_history)
    assert np.all(np.diff(hist) < 0), "every accepted swap must strictly improve"
    assert res.objective == pytest.approx(weighted_objective(diss, weights, res.medoids))
    assert _is_swap_local_min(diss, weights, res.medoids)


@given(seed=st.integers(0, 10_000), n=st.integers(6, 40), k=st.integers(2, 5))
@settings(max_examples=40, deadline=None)
def test_monotone_and_terminates_under_a_non_metric_dissimilarity(seed, n, k):
    """dE00 violates the triangle inequality; the medoid formulation must not care."""
    rng = np.random.default_rng(seed)
    lab = np.column_stack(
        [rng.uniform(0, 100, n), rng.uniform(-90, 90, n), rng.uniform(-90, 90, n)]
    )
    weights = rng.integers(1, 500, size=n).astype(float)
    diss = delta_e2000_matrix(lab, lab) ** 2
    np.fill_diagonal(diss, 0.0)

    res = weighted_fastpam(diss, weights, k)

    assert res.converged
    assert np.all(np.diff(res.objective_history) < 0)
    assert _is_swap_local_min(diss, weights, res.medoids)


def test_finds_the_global_optimum_on_small_separated_problems():
    rng = np.random.default_rng(3)
    pts = _blobs(rng, [(0, 0), (30, 0), (0, 30)], per_blob=4, spread=0.5)
    weights = rng.integers(1, 50, size=len(pts)).astype(float)
    diss = _euclid(pts)

    res = weighted_fastpam(diss, weights, 3)

    assert res.objective == pytest.approx(_brute_force_optimum(diss, weights, 3))


def test_uniform_weights_match_kmedoids_fasterpam_and_pam():
    rng = np.random.default_rng(11)
    pts = _blobs(rng, [(0, 0, 0), (40, 0, 0), (0, 40, 0), (0, 0, 40)], per_blob=60, spread=2.0)
    diss = _euclid(pts)
    weights = np.ones(len(pts))

    ours = weighted_fastpam(diss, weights, 4)
    fp = kmedoids.fasterpam(diss, 4, random_state=0)
    pam = kmedoids.pam(diss, 4)

    assert ours.objective == pytest.approx(pam.loss, rel=1e-9)
    assert ours.objective == pytest.approx(fp.loss, rel=1e-9)
    assert set(ours.medoids.tolist()) == set(int(m) for m in pam.medoids)


def test_integer_weights_equal_duplicating_points_for_kmedoids():
    rng = np.random.default_rng(5)
    pts = _blobs(rng, [(0, 0), (25, 5), (-10, 30)], per_blob=25, spread=1.5)
    weights = rng.integers(1, 20, size=len(pts))
    diss = _euclid(pts)

    ours = weighted_fastpam(diss, weights.astype(float), 3)

    dup_idx = np.repeat(np.arange(len(pts)), weights)
    dup_diss = diss[np.ix_(dup_idx, dup_idx)]
    ref = kmedoids.pam(dup_diss, 3)

    assert ours.objective == pytest.approx(ref.loss, rel=1e-9)


def test_weights_actually_steer_the_medoids():
    """A far-away group only earns a medoid if its mass is large enough; this is
    why the histogram weights (pixel counts) have to be honored, not dropped."""
    pts = np.array([[0.0], [1.0], [2.0], [3.0], [100.0], [101.0]])
    diss = _euclid(pts) ** 2

    light = weighted_fastpam(diss, np.array([100, 100, 100, 100, 1, 1], float), 1)
    heavy = weighted_fastpam(diss, np.array([1, 1, 1, 1, 100, 100], float), 1)
    assert light.medoids[0] in (1, 2)
    assert heavy.medoids[0] in (4, 5)

    # k=2: the tiny far group still gets its own medoid because squared
    # distance to it would otherwise dominate.
    two = weighted_fastpam(diss, np.array([100, 100, 100, 100, 1, 1], float), 2)
    assert {int(pts[m, 0] > 50) for m in two.medoids} == {0, 1}


def test_build_returns_k_distinct_points_and_is_deterministic():
    rng = np.random.default_rng(0)
    pts = rng.normal(size=(50, 3))
    diss = _euclid(pts)
    w = rng.integers(1, 10, size=50).astype(float)
    a = weighted_build(diss, w, 6)
    b = weighted_build(diss, w, 6)
    assert len(set(a.tolist())) == 6
    assert np.array_equal(a, b)


def test_k_equals_one_and_k_equals_n():
    rng = np.random.default_rng(1)
    pts = rng.normal(size=(9, 2))
    diss = _euclid(pts)
    w = rng.integers(1, 10, size=9).astype(float)

    one = weighted_fastpam(diss, w, 1)
    assert one.medoids[0] == int(np.argmin(w @ diss))

    full = weighted_fastpam(diss, w, 9)
    assert full.objective == 0.0
    assert sorted(full.medoids.tolist()) == list(range(9))


@pytest.mark.parametrize("bad_k", [0, 10])
def test_rejects_invalid_k(bad_k):
    diss = _euclid(np.random.default_rng(0).normal(size=(9, 2)))
    with pytest.raises(ValueError):
        weighted_fastpam(diss, np.ones(9), bad_k)


def test_rejects_non_positive_weights():
    diss = _euclid(np.random.default_rng(0).normal(size=(5, 2)))
    with pytest.raises(ValueError):
        weighted_fastpam(diss, np.array([1, 1, 0, 1, 1], float), 2)


def test_de00_wrapper_recovers_known_lab_clusters():
    lab = np.array(
        [
            [50, 0, 0], [51, 1, 0], [49, 0, 1],  # grey
            [55, 70, 50], [56, 71, 49], [54, 69, 51],  # red
            [30, 20, -70], [31, 21, -69], [29, 19, -71],  # blue
        ],
        dtype=float,
    )  # fmt: skip
    w = np.array([10, 30, 10, 5, 50, 5, 20, 20, 60], float)

    res = cluster_lab_medoids_de00(lab, w, 3)

    assert res.converged
    # one medoid per color group, and the labels split exactly along those groups
    groups = [{0, 1, 2}, {3, 4, 5}, {6, 7, 8}]
    assert [len(g & set(res.medoids.tolist())) for g in groups] == [1, 1, 1]
    for g in groups:
        assert len({int(res.labels[i]) for i in g}) == 1
    # The medoid is the weighted minimizer, not the heaviest member: in the blue
    # group, points 7 and 8 are ~6.4 dE00^2 apart but each ~1.6 from point 6, so
    # 6 wins despite 8 carrying triple its mass.
    assert res.medoids[res.labels[6]] == 6
