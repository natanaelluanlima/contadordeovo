from egg_counter.detection import Detection, _consensus_merge


def test_consensus_keeps_agreement_between_models() -> None:
    model_a = [
        Detection(bbox=(10, 10, 50, 50), confidence=0.7, label="egg"),
        Detection(bbox=(100, 100, 140, 140), confidence=0.4, label="egg"),
    ]
    model_b = [
        Detection(bbox=(12, 12, 52, 52), confidence=0.65, label="egg"),
    ]
    merged = _consensus_merge(
        [model_a, model_b],
        iou_threshold=0.45,
        solo_confidence=0.55,
    )
    assert len(merged) == 1
    assert merged[0].label == "egg"
    assert merged[0].confidence >= 0.7


def test_consensus_keeps_high_confidence_solo() -> None:
    model_a = [Detection(bbox=(10, 10, 50, 50), confidence=0.9, label="egg")]
    model_b: list[Detection] = []
    merged = _consensus_merge(
        [model_a, model_b],
        iou_threshold=0.45,
        solo_confidence=0.55,
    )
    assert len(merged) == 1


def test_consensus_drops_low_confidence_solo() -> None:
    model_a = [Detection(bbox=(10, 10, 50, 50), confidence=0.4, label="egg")]
    model_b: list[Detection] = []
    merged = _consensus_merge(
        [model_a, model_b],
        iou_threshold=0.45,
        solo_confidence=0.55,
    )
    assert merged == []
