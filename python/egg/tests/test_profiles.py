from egg_counter.config import detect_video_profile, load_named_video_profile


def test_detect_video_profile() -> None:
    assert detect_video_profile(960, 540) == "padrao"
    assert detect_video_profile(848, 478) == "testes"
    assert detect_video_profile(1280, 720) is None


def test_load_named_video_profile() -> None:
    camera, runtime = load_named_video_profile("testes")
    assert camera.width == 848
    assert camera.height == 478
    assert runtime.match_distance == 100.0
