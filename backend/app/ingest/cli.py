"""CLI entrypoint for dataset ingestion.

    python -m app.ingest.cli --dataset rico --path /data/rico/unique_uis

Requires DATABASE_URL to be set (see backend/.env.example) -- ingestion's
whole point is populating the Postgres histogram cache, so it refuses to
run without one rather than silently doing nothing.

Downloading the dataset itself is a separate, human-run step; this script
only ever reads files that are already on local disk.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from app.db import DATABASE_URL, get_db_session, init_db
from app.ingest.pipeline import ingest_dataset

_DATASETS = {"rico", "enrico", "webui"}

# The decode/resize/Lab/bin step is CPU-bound and dominates wall-clock
# time (~250-350ms/image vs. ~5ms for the Postgres write), so it's worth
# parallelizing by default; leave a couple of cores free for the OS/DB.
_DEFAULT_WORKERS = max(1, (os.cpu_count() or 2) - 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=sorted(_DATASETS))
    parser.add_argument(
        "--path", required=True, type=Path, help="Directory containing the downloaded images"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=_DEFAULT_WORKERS,
        help=f"Parallel worker processes for decode/resize/binning (default: {_DEFAULT_WORKERS})",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.path.is_dir():
        print(f"Not a directory: {args.path}", file=sys.stderr)
        return 1

    if not DATABASE_URL:
        print("DATABASE_URL is not set; nothing to ingest into.", file=sys.stderr)
        return 1

    init_db()
    session = next(get_db_session())
    try:
        summary = ingest_dataset(session, args.dataset, args.path, workers=args.workers)
    finally:
        session.close()

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
