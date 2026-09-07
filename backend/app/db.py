"""Database engine/session setup for the histogram cache.

Caching is opt-in: with no DATABASE_URL set, get_db_session yields None and
extract_palette runs exactly as it did before this module existed.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.cache.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None

if DATABASE_URL:
    _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db() -> None:
    """Create the cache tables if needed. Best-effort: an unreachable
    Postgres disables caching rather than blocking API startup."""
    if _engine is None:
        logger.info("DATABASE_URL not set; histogram cache disabled")
        return
    try:
        Base.metadata.create_all(_engine)
    except Exception:
        logger.exception("Could not initialize histogram cache database; continuing without it")


def get_db_session() -> Iterator[Session | None]:
    if _SessionLocal is None:
        yield None
        return
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
