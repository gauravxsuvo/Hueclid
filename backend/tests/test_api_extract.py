"""API-level smoke tests for POST /api/v1/extract and GET /health."""
from __future__ import annotations

import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.color.deltae2000 import delta_e2000
from app.color.srgb_lab import srgb_to_lab
from app.main import app

client = TestClient(app)


def _png_bytes(color=(200, 30, 30), size=(64, 64)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_extract_returns_palette_matching_input_color():
    color = (200, 30, 30)
    files = {"file": ("test.png", _png_bytes(color), "image/png")}
    resp = client.post("/api/v1/extract", files=files, params={"k": 3})
    assert resp.status_code == 200

    body = resp.json()
    assert body["k"] == 1  # single flat color -> exactly one histogram bin
    assert len(body["palette"]) == 1
    assert body["palette"][0]["weight"] == 1.0

    expected_lab = srgb_to_lab(np.array(color, dtype=np.float64))
    got_lab = np.array(body["palette"][0]["lab"])
    assert delta_e2000(got_lab, expected_lab) < 0.5


def test_extract_rejects_unsupported_content_type():
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    resp = client.post("/api/v1/extract", files=files)
    assert resp.status_code == 415


def test_extract_rejects_empty_file():
    files = {"file": ("test.png", b"", "image/png")}
    resp = client.post("/api/v1/extract", files=files)
    assert resp.status_code == 400


def test_extract_rejects_corrupt_image():
    files = {"file": ("test.png", b"\x89PNGnotactuallyapng", "image/png")}
    resp = client.post("/api/v1/extract", files=files)
    assert resp.status_code == 400


def test_extract_k_query_param_is_respected():
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:20] = [250, 250, 250]
    arr[20:40] = [30, 90, 200]
    arr[40:60] = [20, 20, 20]
    arr[60:80] = [200, 30, 30]
    arr[80:100] = [30, 180, 90]
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    files = {"file": ("test.png", buf.getvalue(), "image/png")}
    resp = client.post("/api/v1/extract", files=files, params={"k": 5})
    assert resp.status_code == 200
    assert resp.json()["k"] == 5


def test_extract_k_out_of_range_is_rejected():
    files = {"file": ("test.png", _png_bytes(), "image/png")}
    resp = client.post("/api/v1/extract", files=files, params={"k": 50})
    assert resp.status_code == 422
