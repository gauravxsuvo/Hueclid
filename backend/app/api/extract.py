"""POST /api/v1/extract -- image in, ranked palette out."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.clustering.kmeans import extract_palette

router = APIRouter(prefix="/api/v1", tags=["extract"])

_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
_ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.post("/extract")
async def extract(
    file: UploadFile = File(...),
    k: int = Query(5, ge=1, le=12, description="Number of palette colors to extract"),
) -> dict:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type: {file.content_type!r}. "
            f"Allowed: {sorted(_ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")

    try:
        return extract_palette(image_bytes, k=k)
    except Exception as exc:  # noqa: BLE001 -- surface as a 400, not a 500
        raise HTTPException(status_code=400, detail=f"Could not process image: {exc}") from exc
