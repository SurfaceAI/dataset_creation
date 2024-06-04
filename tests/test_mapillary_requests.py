import sys

# setting path
sys.path.append("mapillary")
sys.path.append("./")

import mercantile
import pytest
import requests
from vt2geojson.tools import vt_bytes_to_geojson

from mapillary import mapillary_requests


@pytest.fixture(scope="module")
def token_path():
    return "mapillary_token.txt"


# load mapillary access token
def test_load_mapillary_token(token_path):
    access_token = mapillary_requests.load_mapillary_token(token_path=token_path)

    assert access_token.startswith("MLY|")


@pytest.fixture(scope="module")
def access_token(token_path):
    return mapillary_requests.load_mapillary_tokens(token_path=token_path)[0]


# TODO:
### request mapillary data from vector tiles endpoint

# # get list of vector tiles intersecting a bbox
# def bbox_to_tiles_list(west, south, east, north):
#     return list(mercantile.tiles(west, south, east, north, 14))

# # request metadata for a tile
# def request_image_data_from_tile_endpoint(tile, access_token):

#     # define vector tile endpoint
#     tile_coverage = 'mly1_public'
#     # define tile layer
#     tile_layer = "image"

#     # request url for tile data
#     tile_url = 'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}?access_token={}'.format(tile_coverage,tile.z,tile.x,tile.y,access_token)
#     response = requests.get(tile_url)
#     data = vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z,layer=tile_layer)

#     return data["features"]

# # extract image id from a single tile metadata feature
# def extract_image_id_from_tile(index, feature):
#     return feature['properties']['id']

# # extract image coordinates [lng, lat] from a single tile metadata feature
# def extract_image_coord_from_tile(index, feature):
#     return feature["geometry"]["coordinates"]


### request mapillary data from image endpoint

# request metadata for a single image


class TestRequestImageDataFromImageEntity:
    def test_simple_request(self, access_token):
        image_id = "109662244529983"

        data = mapillary_requests.request_image_data_from_image_entity(
            image_id, access_token
        )

        assert "id" in data
        assert data["id"] == image_id
        assert "thumb_1024_url" in data
        assert "detections" in data


@pytest.fixture(scope="module")
def image_data(access_token):
    image_id = "109662244529983"
    data = mapillary_requests.request_image_data_from_image_entity(
        image_id, access_token
    )
    return data


# extract image detections from image data


def test_extract_detections_from_image(image_data):
    detections = mapillary_requests.extract_detections_from_image(image_data)

    assert isinstance(detections, list)
    assert all(
        key in detections[0] for key in ("value", "geometry", "created_at", "id")
    )


# extract image url from image data
def test_extract_url_from_image(image_data):
    url = mapillary_requests.extract_url_from_image(image_data)

    assert url.startswith("https")


def test_download_image(image_data):
    url = mapillary_requests.extract_url_from_image(image_data)
    image_raw = mapillary_requests.download_image(url)

    assert isinstance(image_raw, (bytes, bytearray))
