"""Typed response models shared by the extraction API and its consumers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ImageSize(BaseModel):
    width: int
    height: int


class PaletteSwatch(BaseModel):
    rank: int
    hex: str
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    weight: float = Field(ge=0.0, le=1.0)


class ViewerAxes(BaseModel):
    x: Literal["a*"] = "a*"
    y: Literal["L*"] = "L*"
    z: Literal["b*"] = "b*"


class ViewerPoint(BaseModel):
    lab: tuple[float, float, float]
    rgb: tuple[int, int, int]
    weight: float = Field(ge=0.0, le=1.0)
    cluster: int = Field(ge=0)


class VisualizationPayload(BaseModel):
    """Versioned, bounded payload for visual clients such as the 3D Lab viewer."""

    schema_version: Literal[1] = 1
    space: Literal["cielab-d65"] = "cielab-d65"
    axes: ViewerAxes = Field(default_factory=ViewerAxes)
    points: list[ViewerPoint]
    total_bins: int = Field(ge=0)
    displayed_bins: int = Field(ge=0)
    displayed_weight: float = Field(ge=0.0, le=1.0)
    truncated: bool


class ExtractResult(BaseModel):
    palette: list[PaletteSwatch]
    k: int = Field(ge=1)
    image_size: ImageSize
    histogram_bins: int = Field(ge=1)
    visualization: VisualizationPayload | None = None
