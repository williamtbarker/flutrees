"""Validated presentation settings and bounded viewport geometry."""

from dataclasses import dataclass
import math
from typing import Any


FIGURE_FIELDS = ("figure_width", "figure_height", "level_spacing", "node_spacing", "line_width")


def finite_number(value: Any, name: str, minimum: float, maximum: float) -> None:
    """Reject Booleans, strings, NaN and infinities without implicit coercion."""
    if type(value) not in (int, float) or not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number between {minimum:g} and {maximum:g}.")


@dataclass(frozen=True)
class FigureStyle:
    figure_width: float = 14.0
    figure_height: float = 8.5
    level_spacing: float = 1.0
    node_spacing: float = 1.0
    line_width: float = 1.5

    def __post_init__(self) -> None:
        finite_number(self.figure_width, "Figure width", 6, 30)
        finite_number(self.figure_height, "Figure height", 4, 24)
        finite_number(self.level_spacing, "Level spacing", 0.25, 4)
        finite_number(self.node_spacing, "Node spacing", 0.25, 4)
        finite_number(self.line_width, "Line width", 0.25, 5)


def image_size(width: int, height: int, viewport_width: int, viewport_height: int,
               zoom: float = 1.0) -> tuple[int, int]:
    """Fit with at most 2x native enlargement; bound relative zoom allocation."""
    for value in (width, height, viewport_width, viewport_height):
        if type(value) is not int or not 1 <= value <= 1_000_000:
            raise ValueError("Image and viewport dimensions must be integers from 1 to 1,000,000.")
    finite_number(zoom, "Zoom", 0.25, 8)
    scale = min(2.0, viewport_width / width, viewport_height / height) * zoom
    scale = min(scale, math.sqrt(8_000_000 / (width * height)), 8000 / max(width, height))
    return max(1, int(width * scale)), max(1, int(height * scale))
