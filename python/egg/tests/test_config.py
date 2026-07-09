from pathlib import Path

import pytest

from egg_counter.config import load_camera_config, load_runtime_config


def test_load_camera_config_resolves_video_path(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"fake")
    config_file = tmp_path / "camera.yaml"
    config_file.write_text(
        "\n".join(
            [
                'source: "sample.mp4"',
                "width: 640",
                "height: 480",
            ]
        ),
        encoding="utf-8",
    )

    camera = load_camera_config(config_file)

    assert camera.source == str(video.resolve())


def test_load_runtime_config_resolves_reference_image(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    reference = config_dir / "reference.jpg"
    reference.write_bytes(b"fake")
    config_file = config_dir / "runtime.yaml"
    config_file.write_text(
        "\n".join(
            [
                "backend: classic",
                'reference_image: "config/reference.jpg"',
            ]
        ),
        encoding="utf-8",
    )

    runtime = load_runtime_config(config_file)

    assert runtime.reference_image == str(reference.resolve())


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("- item\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalido"):
        load_runtime_config(config_file)
