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
    tracker = CentroidTracker(max_distance=50.0, max_missing=2)
    tracker.update([Detection(bbox=(10, 10, 30, 30), confidence=0.9, label="egg")])

    tracker.update([])
    tracker.update([])
    tracker.update([])

    assert tracker.active_track_count == 0
