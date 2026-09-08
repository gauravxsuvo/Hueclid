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
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache.histogram_cache import store_bins
from app.cache.models import DatasetImage
from app.clustering.kmeans import _A_STEP, _B_STEP, _L_STEP, ImageTooLargeError, compute_lab_bins

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


def ingest_dataset(
    session: Session, dataset: str, root: Path, log_every: int = 200, workers: int = 1
) -> dict:
    """Walks `root` and ingests every image under it.

    Idempotent and resumable: a file already recorded for this dataset
    (by relative path) is skipped without being re-read or re-hashed, so
    an interrupted run can just be restarted.

    `workers` > 1 farms the CPU-bound decode/resize/Lab/bin step out to a
    process pool -- that step (~250-350ms/image) dominates wall-clock
    time and is embarrassingly parallel across images, unlike the actual
    Postgres write (~5ms/image, not worth parallelizing). Defaults to 1
    (fully sequential, no subprocesses) to keep the common/test path
    simple and deterministic; the CLI picks a higher default for real runs.
    """
    if workers <= 1:
        return _ingest_dataset_sequential(session, dataset, root, log_every)
    return _ingest_dataset_parallel(session, dataset, root, log_every, workers)


def _ingest_dataset_sequential(session: Session, dataset: str, root: Path, log_every: int) -> dict:
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


def _bin_one_file(args: tuple[Path, Path]) -> dict:
    """Runs in a worker process: pure CPU work (decode/resize/Lab/bin), no
    DB session crosses the process boundary -- SQLAlchemy sessions aren't
    fork/spawn-safe. The parent process does the (fast) DB write.
    """
    root, path = args
    relpath = path.relative_to(root).as_posix()
    try:
        image_bytes = path.read_bytes()
        bins = compute_lab_bins(image_bytes, db_session=None)
    except ImageTooLargeError as exc:
        return {"relpath": relpath, "ok": False, "reason": str(exc)}
    except Exception as exc:  # noqa: BLE001 -- report to the parent, don't crash the worker
        return {"relpath": relpath, "ok": False, "reason": repr(exc)}
    return {"relpath": relpath, "ok": True, "bins": bins}


def _ingest_dataset_parallel(
    session: Session, dataset: str, root: Path, log_every: int, workers: int
) -> dict:
    already = {
        row.relpath for row in session.query(DatasetImage.relpath).filter_by(dataset=dataset)
    }
    todo = [p for p in iter_dataset_images(root) if p.relative_to(root).as_posix() not in already]

    n_seen = 0
    n_ingested = 0
    n_skipped = 0
    n_already_cached = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(_bin_one_file, ((root, p) for p in todo), chunksize=4):
            n_seen += 1
            if not result["ok"]:
                logger.warning("Skipping %s: %s", result["relpath"], result["reason"])
                n_skipped += 1
                continue

            bins = result["bins"]
            try:
                # Workers compute with no db_session (a session can't cross
                # the process boundary), so the cache write happens here.
                store_bins(
                    session,
                    bins["image_hash"],
                    bins["bin_points"],
                    bins["weights"],
                    bins["width"],
                    bins["height"],
                    _L_STEP,
                    _A_STEP,
                    _B_STEP,
                )
                session.merge(
                    DatasetImage(
                        dataset=dataset,
                        relpath=result["relpath"],
                        image_hash=bins["image_hash"],
                        width=bins["width"],
                        height=bins["height"],
                    )
                )
                session.commit()
            except SQLAlchemyError:
                logger.warning("Could not record ingestion of %s", result["relpath"], exc_info=True)
                session.rollback()
                n_skipped += 1
                continue

            n_ingested += 1
            if bins["cache_hit"]:
                n_already_cached += 1

            if n_seen % log_every == 0:
                logger.info(
                    "%s: processed %d/%d images (%d ingested, %d skipped)",
                    dataset,
                    n_seen,
                    len(todo),
                    n_ingested,
                    n_skipped,
                )

    return {
        "dataset": dataset,
        "seen": n_seen + len(already),
        "ingested": n_ingested,
        "skipped": n_skipped + len(already),
        "already_cached": n_already_cached,
    }
