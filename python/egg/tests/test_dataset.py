from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from egg_counter.dataset import extract_frames_from_video, extract_frames_from_videos


def _write_test_video(path: Path, *, fps: float = 10.0, frames: int = 30) -> None:
    height, width = 48, 64
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        fps,
        (width, height),
    )
    assert writer.isOpened()
    try:
        for index in range(frames):
            frame = np.full((height, width, 3), index % 255, dtype=np.uint8)
            writer.write(frame)
    finally:
        writer.release()


def test_extract_frames_from_video_one_per_second(tmp_path: Path) -> None:
    video = tmp_path / "sample.avi"
    _write_test_video(video, fps=10.0, frames=30)
    output = tmp_path / "out"

    result = extract_frames_from_video(video, output, interval_seconds=1.0)

    assert result.frames_saved == 3
    assert len(list(output.glob("*.jpg"))) == 3
    assert (output / "sample_000000.jpg").exists()


def test_extract_frames_from_videos_creates_dataset_layout(tmp_path: Path) -> None:
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    _write_test_video(videos_dir / "a.avi", fps=5.0, frames=10)
    _write_test_video(videos_dir / "b.avi", fps=5.0, frames=10)
    dataset = tmp_path / "dataset"

    results = extract_frames_from_videos(videos_dir, dataset, interval_seconds=1.0)

    assert len(results) == 2
    assert (dataset / "images" / "a").is_dir()
    assert (dataset / "images" / "b").is_dir()
    assert (dataset / "labels").is_dir()
    assert sum(item.frames_saved for item in results) == 4


def test_extract_frames_rejects_invalid_interval(tmp_path: Path) -> None:
    video = tmp_path / "sample.avi"
    _write_test_video(video, frames=5)

    with pytest.raises(ValueError):
        extract_frames_from_video(video, tmp_path / "out", interval_seconds=0)
