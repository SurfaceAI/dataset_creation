import base64

import mapbox_vector_tile
import mapillary_requests
import numpy as np
from PIL import Image, ImageDraw
from road_types import RoadTypes, road_types
from shapely import Polygon
from shapely.ops import unary_union

### helper functions, general pre- and post calculations and transformations


# get value from dictionary by a given key
def get_value_from_dict(key, dict: dict):
    try:
        return dict[key]
    except KeyError:
        raise KeyError(f"No key '{key}' in dictionary found.")


# decode geometry from a single encoded detection
def decode_detection_geometry(detection: str):
    decoded_data = base64.decodebytes(detection.encode("utf-8"))
    decoded_geometry = mapbox_vector_tile.decode(decoded_data)
    features = get_value_from_dict(
        "features", get_value_from_dict("mpy-or", decoded_geometry)
    )

    geometry = []
    # a single detection may consist of multiple segments (called features),
    # every segment is a list of polygons
    # (polygons may be f. ex. surface, lane mark, manhole for one road)
    for feature in features:
        geometry.extend(
            get_value_from_dict("coordinates", get_value_from_dict("geometry", feature))
        )

    return geometry


# convert a detection segment to a shapely polygon object
def convert_to_polygon(segment: list[list[float]]):
    return Polygon(list(map(tuple, segment)))


# merge geometry polygons
def merge_polygons(polygons: list[Polygon]):
    return unary_union(polygons)


# calculate area of geometry
def calculate_polygon_area(polygon: Polygon):
    return polygon.area


# generate bounding box (minx, miny, maxx, maxy)
def generate_polygon_bbox(polygon: Polygon):
    return polygon.bounds


# crop image by bbox
def crop_image_by_bbox(image: Image, bbox: tuple[float, float, float, float]):
    image_flip = image.copy().transpose(Image.FLIP_TOP_BOTTOM)
    image_flip_crop = image_flip.crop(bbox)
    image_crop = image_flip_crop.transpose(Image.FLIP_TOP_BOTTOM)

    return image_crop


# transform a detection segment to fit image size
def rescale_detection_to_image_size(segment: list[list[float]], size: tuple[int, int]):
    return np.multiply(np.divide(segment, 4096), size)


# decode and rescale list of detections
def process_detections(detection_list, size: tuple[int, int]):
    processed_list = []
    for detection in detection_list:
        for segment in decode_detection_geometry(detection):
            processed_list.append(rescale_detection_to_image_size(segment, size))

    return processed_list


# draw a polygon on image
def draw_polygon(draw: ImageDraw, polygon: np.ndarray, color):
    draw.polygon(polygon.flatten().tolist(), fill=color)


# create mask of polygons
def create_mask(detection_list, size: tuple[int, int]):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    # map(lambda polygon: draw_polygon(draw, polygon, color=255), process_detections(detection_list, size))
    for polygon in process_detections(detection_list, size):
        draw_polygon(draw, polygon, color=255)

    mask = mask.copy().transpose(Image.FLIP_TOP_BOTTOM)
    return mask


### extract detections


# is a given road type present
# detections are in a dictionary with the following structure:
# {
#     "data": [
#         {
#             ...,
#             "value": "construction--barrier--curb",
#             "geometry": "GiB4AgoGbXB5LW9yKIAgEhEYAwgBIgsJ9CuaJRIcAAAMDw==",
#             "created_at": "2021-08-03T07:01:12+0000",
#             "id": "131850122441807",
#             ...
#         },
#         {
#             ...,
#             "value": "construction--barrier--fence",
#             "geometry": "GiZ4AgoGbXB5LW9yKIAgEhcYAwgBIhEJ0iuyJCoGFQgABAwDAAMKDw==",
#             "created_at": "2021-08-03T07:01:12+0000",
#             "id": "131850125775140",
#             ...
#         },
#     ]
# }
def has_road_type(detections: dict, road_type, types=road_types):
    data = get_value_from_dict("data", detections)

    return any(
        get_value_from_dict("value", detection) in types[road_type]["detections"]
        for detection in data
    )


# get encoded detections of specific road type
def filter_detections(detections: dict, road_type, types=road_types):
    data = get_value_from_dict("data", detections)

    return [
        get_value_from_dict("geometry", detection)
        for detection in data
        if get_value_from_dict("value", detection) in types[road_type]["detections"]
    ]


### different techniques to apply detection to image


## crop bounding box containing all areas of interest
def crop_all_areas_image(image: Image, detection_list):
    polygons = [
        convert_to_polygon(detection)
        for detection in process_detections(detection_list, image.size)
    ]

    polygon = merge_polygons(polygons)
    bbox = generate_polygon_bbox(polygon)
    image_crop = crop_image_by_bbox(image, bbox)

    return image_crop


## crop bbox of largest part of area of interest
def crop_largest_area_image(image: Image, detection_list):
    polygons = [
        convert_to_polygon(detection)
        for detection in process_detections(detection_list, image.size)
    ]

    polygon = max(
        polygons, key=lambda polygon: calculate_polygon_area(polygon), default=None
    )
    bbox = generate_polygon_bbox(polygon)
    image_crop = crop_image_by_bbox(image, bbox)

    return image_crop


## mask areas of no interest based on encoded detections
def mask_image(image: Image, detection_list, color):
    mask = create_mask(detection_list, image.size)
    image_rgba = image.copy()
    image_rgba.putalpha(mask)
    color_layer = Image.new("RGB", image.size, color).convert("RGBA")
    image_masked = Image.alpha_composite(color_layer, image_rgba).convert("RGB")

    return image_masked


# TODO: define threshold and threshold function
# def calculate_coverage_all_areas(detection_list, image_size: tuple[int, int]):
#     polygons = [convert_to_polygon(detection) for detection in process_detections(detection_list, image_size)]
#     polygon = merge_polygons(polygons)

#     polygon_area = calculate_polygon_area(polygon)
#     image_area = image_size[0] * image_size[1]

#     coverage = polygon_area / image_area

#     return coverage


def calculate_coverage_largest_area(detection_list, image_size: tuple[int, int]):
    polygons = [
        convert_to_polygon(detection)
        for detection in process_detections(detection_list, image_size)
    ]

    polygon_area = max([calculate_polygon_area(polygon) for polygon in polygons])
    image_area = image_size[0] * image_size[1]

    coverage = polygon_area / image_area

    return coverage


# create cropped or masked image by road type
# return Null if image has no or not enought information about this road type


def crop_image_by_road_type_all_areas(
    image_data, road_type, image_size="thumb_1024_url", threshold=0.05
):
    detections = mapillary_requests.extract_detections_from_image(image_data)

    if has_road_type(detections, road_type):
        detection_list = filter_detections(detections, road_type)
        image = mapillary_requests.open_image(image_data, image_size)

        if calculate_coverage_largest_area(detection_list, image.size) > threshold:
            return crop_all_areas_image(image, detection_list)


def crop_image_by_road_type_largest_area(
    image_data, road_type, image_size="thumb_1024_url", threshold=0.05
):
    detections = mapillary_requests.extract_detections_from_image(image_data)

    if has_road_type(detections, road_type):
        detection_list = filter_detections(detections, road_type)
        image = mapillary_requests.open_image(image_data, image_size)

        if calculate_coverage_largest_area(detection_list, image.size) > threshold:
            return crop_largest_area_image(image, detection_list)


def mask_image_by_road_type(
    image_data, road_type, image_size="thumb_1024_url", threshold=0.05
):
    detections = mapillary_requests.extract_detections_from_image(image_data)

    if has_road_type(detections, road_type):
        detection_list = filter_detections(detections, road_type)
        image = mapillary_requests.open_image(image_data, image_size)

        if calculate_coverage_largest_area(detection_list, image.size) > threshold:
            return mask_image(image, detection_list)
