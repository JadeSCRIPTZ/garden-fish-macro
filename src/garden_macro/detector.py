from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


RGB = tuple[int, int, int]


class PixelReader(Protocol):
    def pixel(self, x: int, y: int) -> RGB:
        ...


@dataclass(frozen=True)
class PixelTarget:
    x: int
    y: int
    rgb: RGB
    tolerance: int = 20

    def validate(self, screen_width: int, screen_height: int) -> None:
        if not 0 <= self.x < screen_width or not 0 <= self.y < screen_height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) are outside the screen.")
        if not 0 <= self.tolerance <= 255:
            raise ValueError("Tolerance must be between 0 and 255.")
        for channel in self.rgb:
            if not 0 <= channel <= 255:
                raise ValueError("RGB channels must be between 0 and 255.")


def is_rgb_match(current: RGB, target: RGB, tolerance: int) -> bool:
    return all(abs(current[i] - target[i]) <= tolerance for i in range(3))


def read_match(reader: PixelReader, target: PixelTarget) -> tuple[RGB, bool]:
    current = reader.pixel(target.x, target.y)
    return current, is_rgb_match(current, target.rgb, target.tolerance)
