from egg_counter.models import Detection
from egg_counter.tracking import CentroidTracker


def test_registers_new_detections() -> None:
    tracker = CentroidTracker(max_distance=50.0, max_missing=3)
    detections = [Detection(bbox=(10, 10, 30, 30), confidence=0.9, label="egg")]

    tracked = tracker.update(detections)

    assert len(tracked) == 1
    assert tracked[0].track_id == 1
    assert tracked[0].previous_center is None


def test_matches_nearby_detection_to_existing_track() -> None:
    tracker = CentroidTracker(max_distance=50.0, max_missing=3)
    tracker.update([Detection(bbox=(10, 10, 30, 30), confidence=0.9, label="egg")])

    tracked = tracker.update([Detection(bbox=(12, 12, 32, 32), confidence=0.9, label="egg")])

    assert len(tracked) == 1
    assert tracked[0].track_id == 1
    assert tracked[0].previous_center == (20, 20)


def test_removes_stale_tracks() -> None:
    tracker = CentroidTracker(max_distance=50.0, max_missing=2, min_hits=1)
    tracker.update([Detection(bbox=(10, 10, 30, 30), confidence=0.9, label="egg")])

    coasted = tracker.update([])
    assert len(coasted) == 1
    assert coasted[0].track_id == 1

    tracker.update([])
    tracker.update([])

    assert tracker.active_track_count == 0


def test_coasts_track_while_detection_is_missing() -> None:
    tracker = CentroidTracker(max_distance=50.0, max_missing=5, min_hits=2)
    tracker.update([Detection(bbox=(100, 200, 140, 240), confidence=0.9, label="egg")])
    tracker.update([Detection(bbox=(100, 180, 140, 220), confidence=0.9, label="egg")])

    coasted = tracker.update([])

    assert len(coasted) == 1
    assert coasted[0].track_id == 1
    # Predicted upward motion (bottom_to_top belt)
    assert coasted[0].bbox[1] < 180


def test_unconfirmed_track_does_not_coast() -> None:
    tracker = CentroidTracker(max_distance=50.0, max_missing=5, min_hits=2)
    tracker.update([Detection(bbox=(100, 200, 140, 240), confidence=0.9, label="egg")])

    coasted = tracker.update([])

    assert coasted == []
    assert tracker.active_track_count == 0
