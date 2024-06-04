import os
from io import BytesIO
from pathlib import Path

import mercantile
import requests
from PIL import Image
from vt2geojson.tools import vt_bytes_to_geojson

ROOT_DIR = Path(__file__).parent.parent


# load mapillary access token
def load_mapillary_token(token_path=os.path.join(ROOT_DIR, "mapillary_token.txt")):
    with open(token_path, "r") as file:
        access_token = file.read()

    return access_token

def load_mapillary_tokens(token_path=os.path.join(ROOT_DIR, "mapillary_token.txt")):
    with open(token_path, "r") as file:
        return [line.strip() for line in file.readlines()]

# Bounding Box?

### request mapillary data from vector tiles endpoint


# get list of vector tiles intersecting a bbox
def bbox_to_tiles_list(west, south, east, north):
    return list(mercantile.tiles(west, south, east, north, 14))


# request metadata for a tile
def request_image_data_from_tile_endpoint(tile, access_token):
    # define vector tile endpoint
    tile_coverage = "mly1_public"
    # define tile layer
    tile_layer = "image"

    # request url for tile data
    tile_url = (
        "https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}?access_token={}".format(
            tile_coverage, tile.z, tile.x, tile.y, access_token
        )
    )
    response = requests.get(tile_url)
    data = vt_bytes_to_geojson(
        response.content, tile.x, tile.y, tile.z, layer=tile_layer
    )

    return data["features"]


# extract image id from a single tile metadata feature
def extract_image_id_from_tile(index, feature):
    return feature["properties"]["id"]


# extract image coordinates [lng, lat] from a single tile metadata feature
def extract_image_coord_from_tile(index, feature):
    return feature["geometry"]["coordinates"]


# extract captured_at, compass_angle, creator_id, is_pano, sequence_id ?


### request mapillary data from image endpoint

# request metadata for a single image

# choose fields for download (only a selection of the possible):
# id
# captured_at - timestamp, capture time
# compass_angle - float, original compass angle of the image
# creator - { username: string, id: int }, the username and user ID who owns and uploaded the image
# geometry - GeoJSON Point geometry
# height - int, height of the original image uploaded
# width - int, width of the original image uploaded
# is_pano - boolean, a true or false indicator for whether an image is 360 degree panorama
# sequence - string, ID of the sequence, which is a group of images captured in succession
# detections - JSON object, detections from the image including base64 encoded string of the image segmentation coordinates (.value/.geometry? Nicht verwenden bei bb-filter, da zu große Datenmenge)

# choose image size:
# thumb_256_url - string, URL to the 256px wide thumbnail.
# thumb_1024_url - string, URL to the 1024px wide thumbnail.
# thumb_2048_url - string, URL to the 2048px wide thumbnail.
# thumb_original_url - string, URL to the original wide thumbnail.


def request_image_data_from_image_entity(
    image_id,
    access_token,
    url=True,
    image_size="thumb_1024_url",
    detections=True,
    creator=False,
    captured_at=False,
    compass_angle=False,
    geometry=False,
    height=False,
    width=False,
    is_pano=False,
    sequence=False,
):
    fields = "id"

    if url:
        fields += "," + image_size

    if detections:
        fields += ",detections.value,detections.geometry,detections.created_at"

    if creator:
        fields += ",creator"

    if captured_at:
        fields += ",captured_at"

    if compass_angle:
        fields += ",compass_angle"

    if geometry:
        fields += ",geometry"

    if height:
        fields += ",height"

    if width:
        fields += ",width"

    if is_pano:
        fields += ",is_pano"

    if sequence:
        fields += ",sequence"

    # header for mapillary authorization
    header = {"Authorization": "OAuth {}".format(access_token)}

    # request url for image data
    url = "https://graph.mapillary.com/{}?fields={}".format(image_id, fields)
    response = requests.get(url, headers=header)
    data = response.json()

    return data


# extract image detections from image data
def extract_detections_from_image(image_data):
    return image_data["detections"]["data"]


# extract image url from image data
def extract_url_from_image(image_data, image_size="thumb_1024_url"):
    try:
        return image_data[image_size]
    except KeyError:
        raise KeyError(f"Image size '{image_size}' is not found.")


def download_image(image_url):
    return requests.get(image_url, stream=True).content


def open_image(image_data, image_size="thumb_1024_url"):
    url = extract_url_from_image(image_data, image_size)
    image_raw = download_image(url)
    image = Image.open(BytesIO(image_raw))

    return image
