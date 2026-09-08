"""Dataset ingestion: a small synthetic image tree stands in for a
downloaded Rico/Enrico/WebUI directory (PLAN.md 4.3).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.cache.models import Base, DatasetImage, HistogramCacheEntry
from app.ingest.pipeline import ingest_dataset, iter_dataset_images


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        yield s


def _make_dataset_tree(root: Path) -> None:
    (root / "sub").mkdir()
    Image.new("RGB", (40, 40), color=(200, 30, 30)).save(root / "a.png")
    Image.new("RGB", (40, 40), color=(30, 90, 210)).save(root / "sub" / "b.jpg", format="JPEG")
    (root / "notes.txt").write_text("not an image")
    (root / "corrupt.png").write_bytes(b"\x89PNGnotactuallyapng")


def test_iter_dataset_images_finds_only_images_recursively(tmp_path):
    _make_dataset_tree(tmp_path)
    found = {p.relative_to(tmp_path).as_posix() for p in iter_dataset_images(tmp_path)}
    assert found == {"a.png", "sub/b.jpg", "corrupt.png"}


def test_ingest_dataset_populates_cache_and_skips_bad_files(session, tmp_path):
    _make_dataset_tree(tmp_path)

    summary = ingest_dataset(session, "rico", tmp_path)

    assert summary["seen"] == 3
    assert summary["ingested"] == 2  # a.png, sub/b.jpg
    assert summary["skipped"] == 1  # corrupt.png

    rows = session.query(DatasetImage).all()
    assert {r.relpath for r in rows} == {"a.png", "sub/b.jpg"}
    assert all(r.dataset == "rico" for r in rows)

    cache_rows = session.query(HistogramCacheEntry).all()
    assert len(cache_rows) == 2


def test_ingest_dataset_is_idempotent_and_resumable(session, tmp_path):
    _make_dataset_tree(tmp_path)

    first = ingest_dataset(session, "enrico", tmp_path)
    second = ingest_dataset(session, "enrico", tmp_path)

    assert first["ingested"] == 2
    assert second["ingested"] == 0
    assert second["skipped"] == 3  # everything already recorded (or still corrupt)

    assert session.query(DatasetImage).count() == 2


def test_ingest_dataset_parallel_matches_sequential(session, tmp_path):
    _make_dataset_tree(tmp_path)

    summary = ingest_dataset(session, "rico", tmp_path, workers=2)

    assert summary["seen"] == 3
    assert summary["ingested"] == 2
    assert summary["skipped"] == 1

    rows = {r.relpath for r in session.query(DatasetImage).all()}
    assert rows == {"a.png", "sub/b.jpg"}
    assert session.query(HistogramCacheEntry).count() == 2

    # Resuming with workers>1 also skips already-ingested files.
    second = ingest_dataset(session, "rico", tmp_path, workers=2)
    assert second["ingested"] == 0
    assert second["skipped"] == 3


def test_ingest_dataset_different_datasets_do_not_collide(session, tmp_path):
    _make_dataset_tree(tmp_path)

    ingest_dataset(session, "rico", tmp_path)
    ingest_dataset(session, "enrico", tmp_path)

    assert session.query(DatasetImage).filter_by(dataset="rico").count() == 2
    assert session.query(DatasetImage).filter_by(dataset="enrico").count() == 2
    # Both datasets point at the same bytes, so the histogram cache itself
    # is shared and only has one entry per distinct image.
    assert session.query(HistogramCacheEntry).count() == 2
