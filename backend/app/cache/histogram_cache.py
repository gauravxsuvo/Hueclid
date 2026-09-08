"""Read/write helpers for the histogram cache table.

The cache is strictly an optimization: any database error here is logged
and treated as a cache miss (on read) or silently dropped (on write) so a
missing or unreachable Postgres never breaks /extract, it just makes it
recompute every time.
"""

from __future__ import annotations

import hashlib
import logging

import numpy as np
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache.models import HistogramCacheEntry

logger = logging.getLogger(__name__)


def hash_image_bytes(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def get_cached_bins(
    session: Session,
    image_hash: str,
    l_step: float,
    a_step: float,
    b_step: float,
) -> tuple[np.ndarray, np.ndarray, int, int] | None:
    """Returns (bin_points, weights, width, height) on a hit, else None."""
    try:
        entry = session.get(HistogramCacheEntry, image_hash)
    except SQLAlchemyError:
        logger.warning("Histogram cache read failed; recomputing", exc_info=True)
        return None

    if entry is None:
        return None
    if (entry.l_step, entry.a_step, entry.b_step) != (l_step, a_step, b_step):
        # Grid changed since this entry was cached -- treat as a miss.
        return None

    bin_points = np.frombuffer(entry.bin_points, dtype=np.float64).reshape(entry.n_bins, 3)
    weights = np.frombuffer(entry.weights, dtype=np.int64)
    return bin_points, weights, entry.width, entry.height


def store_bins(
    session: Session,
    image_hash: str,
    bin_points: np.ndarray,
    weights: np.ndarray,
    width: int,
    height: int,
    l_step: float,
    a_step: float,
    b_step: float,
) -> None:
    entry = HistogramCacheEntry(
        image_hash=image_hash,
        width=width,
        height=height,
        n_bins=bin_points.shape[0],
        l_step=l_step,
        a_step=a_step,
        b_step=b_step,
        bin_points=np.ascontiguousarray(bin_points, dtype=np.float64).tobytes(),
        weights=np.ascontiguousarray(weights, dtype=np.int64).tobytes(),
    )
    try:
        session.merge(entry)
        session.commit()
    except SQLAlchemyError:
        logger.warning("Histogram cache write failed; continuing uncached", exc_info=True)
        session.rollback()
