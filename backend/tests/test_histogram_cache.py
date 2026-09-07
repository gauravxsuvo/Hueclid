"""Histogram cache: unit tests against an in-memory SQLite session (the
cache module is SQL-generic, see app/cache/models.py), plus an integration
test that extract_palette actually skips recompute on a cache hit.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.cache.histogram_cache import get_cached_bins, hash_image_bytes, store_bins
from app.cache.models import Base
from app.clustering import kmeans


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        yield s


def test_cache_miss_when_empty(session):
    assert get_cached_bins(session, "deadbeef", 2.0, 2.0, 2.0) is None


def test_store_then_get_round_trips(session):
    bin_points = np.array([[50.0, 1.0, -2.0], [10.0, 20.0, 30.0]])
    weights = np.array([5, 9], dtype=np.int64)

    store_bins(session, "abc123", bin_points, weights, 64, 32, 2.0, 2.0, 2.0)
    result = get_cached_bins(session, "abc123", 2.0, 2.0, 2.0)

    assert result is not None
    got_points, got_weights, width, height = result
    np.testing.assert_array_equal(got_points, bin_points)
    np.testing.assert_array_equal(got_weights, weights)
    assert (width, height) == (64, 32)


def test_get_ignores_entry_with_different_grid(session):
    bin_points = np.array([[50.0, 1.0, -2.0]])
    weights = np.array([1], dtype=np.int64)
    store_bins(session, "abc123", bin_points, weights, 10, 10, 2.0, 2.0, 2.0)

    assert get_cached_bins(session, "abc123", 4.0, 4.0, 4.0) is None


def test_store_twice_overwrites_via_merge(session):
    store_bins(
        session,
        "same-hash",
        np.array([[1.0, 2.0, 3.0]]),
        np.array([1], dtype=np.int64),
        1,
        1,
        2.0,
        2.0,
        2.0,
    )
    store_bins(
        session,
        "same-hash",
        np.array([[9.0, 9.0, 9.0]]),
        np.array([7], dtype=np.int64),
        2,
        2,
        2.0,
        2.0,
        2.0,
    )

    result = get_cached_bins(session, "same-hash", 2.0, 2.0, 2.0)
    got_points, got_weights, width, height = result
    np.testing.assert_array_equal(got_points, np.array([[9.0, 9.0, 9.0]]))
    assert (width, height) == (2, 2)


def test_hash_is_stable_and_content_dependent():
    a = hash_image_bytes(b"hello")
    b = hash_image_bytes(b"hello")
    c = hash_image_bytes(b"world")
    assert a == b
    assert a != c
    assert len(a) == 64


def _make_flat_png(color=(120, 60, 200), size=(50, 50)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_palette_reports_cache_hit_and_skips_recompute(session, monkeypatch):
    image_bytes = _make_flat_png()

    calls = {"n": 0}
    original_decode = kmeans._decode_rgb

    def counting_decode(b: bytes):
        calls["n"] += 1
        return original_decode(b)

    monkeypatch.setattr(kmeans, "_decode_rgb", counting_decode)

    first = kmeans.extract_palette(image_bytes, k=3, db_session=session)
    assert first["cache_hit"] is False
    assert calls["n"] == 1

    second = kmeans.extract_palette(image_bytes, k=3, db_session=session)
    assert second["cache_hit"] is True
    assert calls["n"] == 1  # decode was skipped on the cache hit

    assert first["palette"] == second["palette"]
    assert first["image_size"] == second["image_size"] == {"width": 50, "height": 50}


def test_extract_palette_without_session_behaves_as_before():
    image_bytes = _make_flat_png()
    result = kmeans.extract_palette(image_bytes, k=2)
    assert result["cache_hit"] is False
    assert len(result["palette"]) == 1
