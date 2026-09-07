"""ORM schema for the Postgres histogram cache (PLAN.md 4.3).

Binning is deterministic given the exact uploaded bytes, so the expensive
half of extract_palette -- decode, linear-light resize, sRGB->Lab, and
histogram binning -- is cached keyed by a hash of those bytes.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, LargeBinary, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HistogramCacheEntry(Base):
    __tablename__ = "histogram_cache"

    image_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    n_bins: Mapped[int] = mapped_column(Integer)
    l_step: Mapped[float] = mapped_column(Float)
    a_step: Mapped[float] = mapped_column(Float)
    b_step: Mapped[float] = mapped_column(Float)
    # (n_bins, 3) float64 and (n_bins,) int64 arrays, stored as raw bytes
    # rather than an ARRAY column so the schema works identically on
    # Postgres and on SQLite in tests.
    bin_points: Mapped[bytes] = mapped_column(LargeBinary)
    weights: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
