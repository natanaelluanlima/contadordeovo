from egg_counter.config import LineConfig
from egg_counter.counting import LineCounter
from egg_counter.models import TrackedDetection


def _tracked(
    track_id: int,
    bbox: tuple[int, int, int, int],
    previous_center: tuple[int, int] | None,
) -> TrackedDetection:
    return TrackedDetection(
        bbox=bbox,
        confidence=0.9,
        label="egg",
        track_id=track_id,
        previous_center=previous_center,
    )


def test_counts_bottom_to_top_crossing() -> None:
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line)

    counter.update([_tracked(1, (90, 300, 130, 340), None)])
    events = counter.update([_tracked(1, (90, 220, 130, 260), (110, 300))])

    assert counter.total_count == 1
    assert len(events) == 1
    assert events[0].track_id == 1


def test_ignores_wrong_direction() -> None:
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line)

    counter.update([_tracked(1, (90, 200, 130, 240), None)])
    events = counter.update([_tracked(1, (90, 300, 130, 340), (110, 220))])

    assert counter.total_count == 0
    assert events == []


def test_does_not_count_when_point_is_on_line() -> None:
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line)

    counter.update([_tracked(1, (90, 280, 130, 320), None)])
    events = counter.update([_tracked(1, (90, 250, 130, 290), (110, 270))])

    assert counter.total_count == 0
    assert events == []


def test_counts_each_track_once() -> None:
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line)

    counter.update([_tracked(1, (90, 300, 130, 340), None)])
    counter.update([_tracked(1, (90, 220, 130, 260), (110, 300))])
    events = counter.update([_tracked(1, (90, 200, 130, 240), (110, 220))])

    assert counter.total_count == 1
    assert events == []


def test_counts_late_first_detection_near_line() -> None:
    """Late first sightings without history must not invent a crossing."""
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line)

    events = counter.update([_tracked(1, (90, 235, 130, 275), None)])

    assert counter.total_count == 0
    assert events == []


def test_spatial_cooldown_blocks_duplicate_new_track() -> None:
    line = LineConfig(x1=0, y1=270, x2=960, y2=270, direction="bottom_to_top")
    counter = LineCounter(line, spatial_cooldown_px=38.0)

    counter.update([_tracked(1, (90, 300, 130, 340), None)])
    events = counter.update([_tracked(1, (90, 220, 130, 260), (110, 300))])
    assert len(events) == 1

    # New track id near the same crossing point must not count again
    dup = counter.update([_tracked(99, (95, 215, 135, 255), (110, 295))])
    assert dup == []
    assert counter.total_count == 1
