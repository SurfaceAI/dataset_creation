import sys

# setting path
sys.path.append("mapillary")
# sys.path.append('./')

import os

import numpy as np
import pytest
from PIL import Image, ImageDraw
from shapely import Polygon

from mapillary import mapillary_detections

# # script path for mock functions
# script_dir = os.path.dirname(os.path.realpath(__file__))
# parent_folder_path = os.path.dirname(script_dir)


# TODO: test coverage? edge cases?


### helper functions, general pre- and post calculations and transformations

# get value from dictionary by a given key


@pytest.fixture(scope="class")
def sample_road_types():
    rtypes = road_types = {
        "a": {
            "detections": [
                "det_a1",
                "det_a2",
            ],
        },
        "b": {
            "detections": [
                "det_b1",
                "det_b2",
                "det_b3",
            ],
        },
        "c": {
            "detections": [
                "det_c1",
            ],
        },
    }
    return rtypes


@pytest.fixture(scope="class")
def sample_detections():
    detections = {
        "data": [
            {
                "value": "det_a1",
                "geometry": "Gr8BeAIKBm1weS1vciiAIBIhGAMIASIbCbID/BVSFAkaAAgKBAYACgcGBwwhBQMLCwMPEhkYAwgCIhMJnAS+FjIADwgLFgAMFgscFQAPEhsYAwgDIhUJzgTqFjoIDwwFFAYEFgAaDwATAw8SVRgDCAQiTwn6BIoXggIaABQWABAYFgQGBAYEGg4MCCYIBgwgFGgAIATGAQRsCJgCA5QDBwUDuQEAGwAlD60DAKkBD30hjQEHFQsJByUPEQMZGRsDFQ8=",
                "created_at": "2021-08-03T07:01:12+0000",
                "id": "131850122441807",
            },
            {
                "value": "det_b1",
                "geometry": "GiB4AgoGbXB5LW9yKIAgEhEYAwgBIgsJ9CuaJRIcAAAMDw==",
                "created_at": "2021-08-03T07:01:12+0000",
                "id": "131850122441807",
            },
            {
                "value": "det_b2",
                "geometry": "GiZ4AgoGbXB5LW9yKIAgEhcYAwgBIhEJ0iuyJCoGFQgABAwDAAMKDw==",
                "created_at": "2021-08-03T07:01:12+0000",
                "id": "131850125775140",
            },
        ]
    }
    return detections


@pytest.fixture(scope="class")
def sample_dict():
    return {"a": 1, "b": 2, "c": 3}


class TestGetValueFromDict:
    def test_existing_key(self, sample_dict):
        value = mapillary_detections.get_value_from_dict("b", sample_dict)
        assert value == 2

    def test_nonexisting_key(self, sample_dict):
        with pytest.raises(KeyError):
            mapillary_detections.get_value_from_dict("z", sample_dict)


# decode geometry from a single encoded detection


@pytest.fixture(scope="class")
def sample_decoded_geometry():
    geom = [
        [
            [217, 2690],
            [227, 2695],
            [240, 2695],
            [244, 2690],
            [246, 2687],
            [246, 2682],
            [242, 2679],
            [238, 2673],
            [221, 2676],
            [219, 2682],
            [213, 2684],
            [217, 2690],
        ],
        [
            [270, 2657],
            [270, 2665],
            [274, 2671],
            [285, 2671],
            [291, 2660],
            [285, 2646],
            [274, 2646],
            [270, 2657],
        ],
        [
            [295, 2635],
            [299, 2643],
            [305, 2646],
            [315, 2643],
            [317, 2632],
            [317, 2619],
            [309, 2619],
            [299, 2621],
            [295, 2635],
        ],
        [
            [317, 2619],
            [330, 2619],
            [340, 2608],
            [340, 2600],
            [352, 2589],
            [354, 2586],
            [356, 2583],
            [358, 2570],
            [365, 2564],
            [369, 2545],
            [373, 2542],
            [379, 2526],
            [389, 2474],
            [389, 2458],
            [391, 2359],
            [393, 2305],
            [397, 2165],
            [395, 1963],
            [391, 1966],
            [389, 2059],
            [389, 2073],
            [389, 2092],
            [381, 2307],
            [381, 2392],
            [373, 2455],
            [356, 2526],
            [352, 2537],
            [346, 2542],
            [342, 2561],
            [334, 2570],
            [332, 2583],
            [319, 2597],
            [317, 2608],
            [317, 2619],
        ],
    ]
    return geom


class TestDecodeDetectionGeometry:
    def test_splitted_geometry(
        self, sample_road_types, sample_detections, sample_decoded_geometry
    ):
        detection = mapillary_detections.filter_detections(
            sample_detections, "a", types=sample_road_types
        )[0]
        geometry = mapillary_detections.decode_detection_geometry(detection)
        assert geometry == sample_decoded_geometry


# convert a detection segment to a shapely polygon object


@pytest.fixture(scope="class")
def sample_segment():
    segment = [[0, 0], [0, 1.5], [2, 1.3], [0, 0]]


class TestConvertToPolygon:
    def simple_polygon(self, sample_segment):
        polygon = mapillary_detections.convert_to_polygon(sample_segment)
        assert isinstance(polygon, Polygon)
        ref = Polygon([(0, 0), (0, 1.5), (2, 1.3)])
        assert mapillary_detections.convert_to_polygon(sample_segment) == ref


# crop image by bbox (minx, miny, maxx, maxy)


@pytest.fixture(scope="class")
def sample_image():
    width_half, height_half = 100, 50

    img = Image.new("RGB", (2 * width_half, 2 * height_half), color="white")
    pixels = img.load()

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

    for i in range(2):
        for j in range(2):
            x = i * width_half
            y = j * height_half
            for k in range(width_half):
                for l in range(height_half):
                    pixels[x + k, y + l] = colors[2 * i + j]

    return img


@pytest.fixture(scope="class")
def sample_crop_image_small():
    width_half, height_half = 100, 50

    img = Image.new("RGB", (width_half, height_half), color="white")
    pixels = img.load()

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

    i = 0
    x = 0
    j = 1
    y = 0
    for k in range(width_half):
        for l in range(height_half):
            pixels[x + k, y + l] = colors[2 * i + j]

    return img


@pytest.fixture(scope="class")
def sample_crop_image_large():
    width_half, height_half = 100, 50

    img = Image.new("RGB", (2 * width_half, height_half), color="white")
    pixels = img.load()

    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

    for i in range(2):
        x = i * width_half
        j = 1
        y = 0
        for k in range(width_half):
            for l in range(height_half):
                pixels[x + k, y + l] = colors[2 * i + j]

    return img


class TestCropImageByBbox:
    def test_simple_image(self, sample_image, sample_crop_image_small):
        bbox = (0, 0, 100, 50)

        crop_image = mapillary_detections.crop_image_by_bbox(sample_image, bbox)

        assert isinstance(crop_image, Image.Image)
        assert crop_image == sample_crop_image_small


# transform a detection segment to fit image size


@pytest.fixture(scope="class")
def sample_decoded_detections():
    return [
        [[0, 0], [(100 / 200 * 4096), 0], [0, (50 / 100 * 4096)], [0, 0]],
        [
            [(200 / 200 * 4096), 0],
            [(200 / 200 * 4096), (5.5 / 100 * 4096)],
            [(194.5 / 200 * 4096), 0],
            [(200 / 200 * 4096), 0],
        ],
    ]


@pytest.fixture(scope="class")
def sample_rescaled_detections():
    return np.asarray(
        [
            [[0.0, 0.0], [100.0, 0.0], [0.0, 50.0], [0.0, 0.0]],
            [[200.0, 0.0], [200.0, 5.5], [194.5, 0.0], [200.0, 0.0]],
        ]
    )


class TestRescaleDetectionToImageSize:
    def test_simple_resizing(
        self, sample_decoded_detections, sample_rescaled_detections
    ):
        size = (200, 100)

        polygon_transformed = mapillary_detections.rescale_detection_to_image_size(
            sample_decoded_detections[0], size
        )

        assert (polygon_transformed == sample_rescaled_detections[0]).all()


@pytest.fixture(scope="class")
def sample_detection_names():
    return ["a", "b"]


# decode and rescale list of detections


@pytest.fixture
def mock_decode_detection_geometry(monkeypatch, sample_decoded_detections):
    def mock_function(detection):
        if detection == "a":
            return [sample_decoded_detections[0]]
        else:
            return [sample_decoded_detections[1]]

    monkeypatch.setattr("mapillary_detections.decode_detection_geometry", mock_function)


class TestProcessDetections:
    def test_simple_processing(
        self,
        mock_decode_detection_geometry,
        sample_detection_names,
        sample_rescaled_detections,
    ):
        processed_detections = mapillary_detections.process_detections(
            sample_detection_names, (200, 100)
        )

        assert ((processed_detections == sample_rescaled_detections).all()).all()


class TestDrawPolygon:
    def test_simple_draw(
        self, mock_decode_detection_geometry, sample_rescaled_detections
    ):
        mask = Image.new("L", (200, 100), 0)
        draw = ImageDraw.Draw(mask)

        for polygon in sample_rescaled_detections:
            mapillary_detections.draw_polygon(draw, polygon, 255)

        # mask.show()

        pixels = mask.load()

        assert pixels[0, 0] == 255
        assert pixels[199, 0] == 255
        assert pixels[0, 99] == 0
        assert pixels[199, 99] == 0


class TestCreateMask:
    def test_simple_mask(self, mock_decode_detection_geometry, sample_detection_names):
        mask = mapillary_detections.create_mask(sample_detection_names, (200, 100))
        assert isinstance(mask, Image.Image)

        # mask.show()

        pixels = mask.load()

        assert pixels[0, 0] == 0
        assert pixels[199, 0] == 0
        assert pixels[0, 99] == 255
        assert pixels[199, 99] == 255


### extract detections

# is a given road type present


class TestHasRoadType:
    def test_existing_type(self, sample_road_types, sample_detections):
        assert mapillary_detections.has_road_type(
            sample_detections, "b", types=sample_road_types
        )

    def test_nonexisting_type(self, sample_road_types, sample_detections):
        assert (
            mapillary_detections.has_road_type(
                sample_detections, "c", types=sample_road_types
            )
            == False
        )


# get encoded detections of specific road type


class TestFilterDetections:
    def test_existing_type(self, sample_road_types, sample_detections):
        detection_list = mapillary_detections.filter_detections(
            sample_detections, "b", types=sample_road_types
        )
        assert detection_list == [
            "GiB4AgoGbXB5LW9yKIAgEhEYAwgBIgsJ9CuaJRIcAAAMDw==",
            "GiZ4AgoGbXB5LW9yKIAgEhcYAwgBIhEJ0iuyJCoGFQgABAwDAAMKDw==",
        ]

    def test_nonexisting_type(self, sample_road_types, sample_detections):
        detection_list = mapillary_detections.filter_detections(
            sample_detections, "c", types=sample_road_types
        )
        assert detection_list == []


### different techniques to apply detection to image

## crop bounding box containing all areas of interest


class TestCropAllAreasImage:
    def test_two_simple_polygons(
        self,
        mock_decode_detection_geometry,
        sample_image,
        sample_crop_image_large,
        sample_detection_names,
    ):
        image_crop = mapillary_detections.crop_all_areas_image(
            sample_image, sample_detection_names
        )

        assert isinstance(image_crop, Image.Image)
        assert image_crop == sample_crop_image_large


## crop bbox of largest part of area of interest


class TestCropLargestAreaImage:
    def test_two_simple_polygons(
        self,
        mock_decode_detection_geometry,
        sample_image,
        sample_crop_image_small,
        sample_detection_names,
    ):
        image_crop = mapillary_detections.crop_largest_area_image(
            sample_image, sample_detection_names
        )

        assert isinstance(image_crop, Image.Image)
        assert image_crop == sample_crop_image_small


## mask areas of no interest based on encoded detections


class TestMaskImage:
    def test_two_simple_polygons(
        self, mock_decode_detection_geometry, sample_detection_names, sample_image
    ):
        image_masked = mapillary_detections.mask_image(
            sample_image, sample_detection_names, (255, 255, 255)
        )
        assert isinstance(image_masked, Image.Image)

        pixels = image_masked.load()

        assert pixels[0, 0] == (255, 255, 255)
        assert pixels[199, 0] == (255, 255, 255)
        assert pixels[0, 99] == (0, 255, 0)
        assert pixels[199, 99] == (255, 255, 0)
