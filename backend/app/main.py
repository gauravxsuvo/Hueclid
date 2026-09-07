"""Hueclid backend -- FastAPI app entrypoint."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.extract import router as extract_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Hueclid API", version="0.1.0", lifespan=lifespan)

_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_allowed_origins = os.environ.get("HUECLID_ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extract_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
