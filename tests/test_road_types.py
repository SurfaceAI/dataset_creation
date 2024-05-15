import sys

# setting path
sys.path.append("mapillary")

import pytest

from mapillary.road_types import road_types


def test_road_types_detections():
    assert "car" in road_types
    assert "bike" in road_types
    assert "pedestrian" in road_types
    for key in road_types.keys():
        assert "detections" in road_types[key]
