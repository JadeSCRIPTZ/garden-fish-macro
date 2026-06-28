from garden_macro.detector import PixelTarget, is_rgb_match, read_match


class FakeReader:
    def __init__(self, colors: dict[tuple[int, int], tuple[int, int, int]]) -> None:
        self.colors = colors

    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        return self.colors[(x, y)]


def test_rgb_match_within_tolerance() -> None:
    assert is_rgb_match((250, 100, 175), (255, 105, 180), 10)


def test_rgb_match_outside_tolerance() -> None:
    assert not is_rgb_match((200, 100, 175), (255, 105, 180), 10)


def test_read_match() -> None:
    target = PixelTarget(5, 5, (255, 140, 0), 20)
    reader = FakeReader({(5, 5): (250, 135, 5)})
    rgb, matched = read_match(reader, target)
    assert matched
    assert rgb == (250, 135, 5)
