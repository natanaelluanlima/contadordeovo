from egg_counter.detection import _extract_roboflow_predictions, _roboflow_item_to_xyxy


def test_extract_workflow_predictions() -> None:
    result = [
        {
            "predictions": {
                "image": {"width": 640, "height": 474},
                "predictions": [
                    {
                        "x": 100.0,
                        "y": 50.0,
                        "width": 40.0,
                        "height": 20.0,
                        "confidence": 0.9,
                        "class": "egg",
                    }
                ],
            }
        }
    ]
    preds = _extract_roboflow_predictions(result)
    assert len(preds) == 1
    assert preds[0]["class"] == "egg"


def test_roboflow_center_box_to_xyxy() -> None:
    bbox = _roboflow_item_to_xyxy(
        {"x": 100.0, "y": 50.0, "width": 40.0, "height": 20.0}
    )
    assert bbox == (80, 40, 120, 60)
