"""Dataset ingestion (PLAN.md 4.3 / Phase 2): walk a directory of already
-downloaded UI screenshots and populate the histogram cache, so the
clustering sweep in Phase 3 never has to decode/resize/bin the same image
twice across the whole ablation grid.

This module only ever reads image files already sitting on local disk.
Fetching Rico, Enrico, or WebUI is a human-run step (see AGENT.md's
dataset-download rule), never something triggered from here.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache.models import DatasetImage
from app.clustering.kmeans import ImageTooLargeError, compute_lab_bins

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def iter_dataset_images(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS:
            yield path


def _already_ingested(session: Session, dataset: str, relpath: str) -> bool:
    return session.get(DatasetImage, (dataset, relpath)) is not None


def ingest_image(session: Session, dataset: str, root: Path, path: Path) -> dict | None:
    """Bins and caches one image, recording it as ingested.

    Returns a summary dict, or None if the file was skipped (already
    ingested on a prior run, unreadable, or over the pipeline's size
    ceiling) so a batch run can report accurate counts.
    """
    relpath = path.relative_to(root).as_posix()

    if _already_ingested(session, dataset, relpath):
        return None

    try:
        image_bytes = path.read_bytes()
        bins = compute_lab_bins(image_bytes, db_session=session)
    except ImageTooLargeError as exc:
        logger.warning("Skipping %s: %s", relpath, exc)
        return None
    except Exception:
        logger.exception("Skipping %s: could not process image", relpath)
        return None

    record = DatasetImage(
        dataset=dataset,
        relpath=relpath,
        image_hash=bins["image_hash"],
        width=bins["width"],
        height=bins["height"],
    )
    try:
        session.merge(record)
        session.commit()
    except SQLAlchemyError:
        logger.warning("Could not record ingestion of %s", relpath, exc_info=True)
        session.rollback()

    return {"relpath": relpath, "image_hash": bins["image_hash"], "cache_hit": bins["cache_hit"]}


def ingest_dataset(session: Session, dataset: str, root: Path, log_every: int = 200) -> dict:
    """Walks `root` and ingests every image under it.

    Idempotent and resumable: a file already recorded for this dataset
    (by relative path) is skipped without being re-read or re-hashed, so
    an interrupted run can just be restarted.
    """
    n_seen = 0
    n_ingested = 0
    n_skipped = 0
    n_already_cached = 0

    for path in iter_dataset_images(root):
        n_seen += 1
        result = ingest_image(session, dataset, root, path)
        if result is None:
            n_skipped += 1
        else:
            n_ingested += 1
            if result["cache_hit"]:
                n_already_cached += 1

        if n_seen % log_every == 0:
            logger.info(
                "%s: processed %d images (%d ingested, %d skipped)",
                dataset,
                n_seen,
                n_ingested,
                n_skipped,
            )

    return {
        "dataset": dataset,
        "seen": n_seen,
        "ingested": n_ingested,
        "skipped": n_skipped,
        "already_cached": n_already_cached,
    }
