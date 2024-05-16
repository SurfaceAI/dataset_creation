import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))
sys.path.append(str(Path(os.path.abspath(__file__)).parent))

import csv

import geopandas as gpd
import matplotlib.pyplot as plt
import mercantile
import numpy as np
import pandas as pd
import psycopg2
import requests
from PIL import Image
from psycopg2 import sql
from psycopg2.extras import DictCursor
from shapely.geometry import Point
from vt2geojson.tools import vt_bytes_to_geojson

import config as config
import constants as const
import database_credentials as db

# set access tokens
with open(config.token_path, "r") as file:
    # access_token = tokenfile.readlines()
    access_tokens = [line.strip() for line in file.readlines()]
current_token = 0


def tile_center(xtile, ytile, zoom):
    """Return longitude,latitude centroid coordinates of mercantile tile
    Args:
        xtile (int): x tile coordinate
        ytile (int): y tile coordinate
        zoom (int): zoom level

    Returns:
        (float, float): A tuple of longitude, latitude.
    """
    upperleft = mercantile.ul(xtile, ytile, zoom)
    upperright = mercantile.ul(xtile + 1, ytile, zoom)
    lowerleft = mercantile.ul(xtile, ytile - 1, zoom)

    # not completely exact but good enough for our purposes
    lon = (upperleft.lng + upperright.lng) / 2
    lat = (upperleft.lat + lowerleft.lat) / 2
    return lon, lat


def get_tile_images(tile):
    """Get information about images (img_id, creator_id, captured_at, is_pano, organization_id) contained within given tile (based on tiles endpoint)
    This does not include coordinates of images!

    Args:
        tile(mercantile.Tile): mercantile tile

    Returns:
        dict: all images within tile as json (dict) including properties: img_id, creator_id, captured_at, is_pano, organization_id.
    """
    global current_token

    response = requests.get(
        config.mapillary_tile_url.format(
            config.tile_coverage, int(tile.z), int(tile.x), int(tile.y)
        ),
        params={"access_token": access_tokens[current_token]},
    )

    # if rate limit is reached, try with other access token
    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        current_token = abs(current_token - 1)  # switch between 0 and 1 and try again
        response = requests.get(
            config.mapillary_tile_url.format(
                config.tile_coverage, int(tile.z), int(tile.x), int(tile.y)
            ),
            params={"access_token": access_tokens[current_token]},
        )

    # return response
    return vt_bytes_to_geojson(
        response.content, tile.x, tile.y, tile.z, layer=config.tile_layer
    )


def get_images_metadata(tile):
    """Get metadata for all images within a tile from mapillary (based on https://graph.mapillary.com/:image_id endpoint)
    This includes coordinates of images!

    Args:
        tile(mercantile.Tile): mercantile tile

    Returns:
        tuple(list, list(list))): Metadata of all images within tile, including coordinates, as tuple: first element is list with column names ("header"). Second element is a list of list, each list representing one image.
    """
    global current_token
    header = [
        "tile_id",
        "id",
        "sequence_id",
        "captured_at",
        "compass_angle",
        "is_pano",
        "creator_id",
        "lon",
        "lat",
    ]
    output = list()
    response = requests.get(
        config.mapillary_tile_url.format(
            config.tile_coverage, int(tile.z), int(tile.x), int(tile.y)
        ),
        params={"access_token": access_tokens[current_token]},
    )
    data = vt_bytes_to_geojson(
        response.content, tile.x, tile.y, tile.z, layer=config.tile_layer
    )

    # a feature is a point/image
    # TODO: can this be speed up?
    for feature in data["features"]:
        output.append(
            [
                str(int(tile.x)) + "_" + str(int(tile.y)) + "_" + str(int(tile.z)),
                feature["properties"]["id"],
                feature["properties"]["sequence_id"],
                feature["properties"]["captured_at"],
                feature["properties"]["compass_angle"],
                feature["properties"]["is_pano"],
                feature["properties"]["creator_id"],
                feature["geometry"]["coordinates"][0],
                feature["geometry"]["coordinates"][1],
            ]
        )

    return (header, output)


def download_image(image_id, image_folder):
    """Download image file based on image_id and save to given image_folder

    Args:
        image_id (str): ID of image to download
        image_folder (str): path of folder to save image to
    """
    response = requests.get(
        config.mapillary_graph_url.format(image_id),
        params={
            "fields": config.image_size,
            "access_token": access_tokens[current_token],
        },
    )

    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        print(f"image_id: {image_id}")
    else:
        data = response.json()
        if config.image_size in data:
            image_url = data[config.image_size]

            # image: save each image with ID as filename to directory by sequence ID
            image_name = "{}.jpg".format(image_id)
            image_path = os.path.join(image_folder, image_name)
            with open(image_path, "wb") as handler:
                image_data = requests.get(image_url, stream=True).content
                handler.write(image_data)
        else:
            print(f"no image size {config.image_size} for image {image_id}")


def query_and_write_img_metadata(tiles, out_path):
    """Write metadata of all images in tiles to csv

    Args:
        tiles (df): dataframe with tiles and columns x,y,z,lat,lon
        out_path (str): path to save csv with image metadata of tile to
    """
    # write metadata of all potential images to csv
    with open(out_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        for i in range(0, len(tiles)):
            if i % 10 == 0:
                print(f"{i} tiles of {len(tiles)}")
            tile = tiles.iloc[i,]
            header, output = get_images_metadata(tile)
            if i == 0:
                csvwriter.writerow(header)
            for row in output:
                csvwriter.writerow(row)


def intersect_mapillary_osm(tile_id, table_name):
    """Function to interact with SQL database:
    for a given tile_id, intersect all images within the tile with OSM streets and create columns "surface", "smoothness" and "highway" for the given table_name.
    These columns are filled with values accordring to the OSM intersection.

    Args:
        tile_id (str): tile ID to intersect with OSM
        table_name (str): name of the table to create new columns for
    """
    # start_query = time.time()

    tilex, tiley, zoom = str.split(tile_id, "_")
    bbox = mercantile.bounds(int(tilex), int(tiley), int(zoom))
    with open(config.sql_script_intersect_osm_mapillary_path, "r") as file:
        query = file.read()

    query = query.format(
        bbox0=bbox[0],
        bbox1=bbox[1],
        bbox2=bbox[2],
        bbox3=bbox[3],
        table_name=table_name,
    )

    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname=db.database,
        user=db.user,
        host=db.host,
    )
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(sql.SQL(query))
        conn.commit()

    # end_query = time.time()
    # print(f"{tile_id} took {(round(end_query-start_query))} secs for intersection")


def save_sql_table_to_csv(
    table_name, output_path, columns=None, where_clause="where highway != ''"
):
    """Download table from SQL database and save as csv

    Args:
        table_name (str): name of table to download
        output_path (str): path of csv to save table to
        where_clause (str, optional):Where clause to filter table before storing to csv. Defaults to "where highway != ''".
    """

    # default columns
    if columns is None:
        columns = [
            "id",
            "tile_id",
            "sequence_id",
            "creator_id",
            "captured_at",
            "is_pano",
            "highway",
            "surface",
            "smoothness",
            "cycleway",
            "cycleway_surface",
            "cycleway_smoothness",
            "cycleway_right",
            "cycleway_right_surface",
            "cycleway_right_smoothness",
            "cycleway_left",
            "cycleway_left_surface",
            "cycleway_left_smoothness",
        ]

    with open(config.sql_script_save_db_to_csv_path, "r") as file:
        query = file.read()
    absolute_path = os.path.join(os.getcwd(), output_path)

    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname=db.database,
        user=db.user,
        host=db.host,
    )
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute(
            sql.SQL(
                query.format(
                    table_name=table_name,
                    columns=",".join(columns),
                    where_clause=where_clause,
                    absolute_path=absolute_path,
                )
            )
        )
        conn.commit()
    conn.close()

    # clean table bc trailing whitespace is stored during export # TODO: better way while exporting from SQL?
    df = pd.read_csv(absolute_path)
    for column in columns:
        if (df[column].dtype == "str") | (df[column].dtype == "object"):
            df[column] = df[column].str.strip()
    df.to_csv(absolute_path, index=False)
    print("csv exported from db")


def clean_smoothness(metadata):
    """Clean smoothness column of metadata dataframe according to defined OSM smoothness values

    Args:
        metadata (df): dataframe with image metadata, including column "smoothness"

    Returns:
        df: dataframe with cleaned smoothness column "smoothness_clean"
    """
    metadata["smoothness"] = metadata.smoothness.str.strip()
    metadata["smoothness_clean"] = metadata["smoothness"].replace(
        [
            "horrible",
            "very_horrible",
            "impassable",
        ],
        const.VERY_BAD,
    )

    metadata["smoothness_clean"] = metadata["smoothness_clean"].replace(
        ["perfect", "very_good"], const.EXCELLENT
    )
    return metadata


def clean_surface(metadata):
    """Clean surface column of metadata dataframe according to defined OSM surface values

    Args:
        metadata (df): dataframe with image metadata, including column "surface"

    Returns:
        df: dataframe with cleaned surface column "surface_clean"
    """
    metadata["surface"] = metadata.surface.str.strip()
    metadata["surface_clean"] = metadata["surface"].replace(
        [
            "compacted",
            "gravel",
            "ground",
            "fine_gravel",
            "dirt",
            "grass",
            "earth",
            "sand",
        ],
        const.UNPAVED,
    )
    metadata["surface_clean"] = metadata["surface_clean"].replace(
        ["cobblestone", "unhewn_cobblestone"], "sett"
    )
    metadata["surface_clean"] = metadata["surface_clean"].replace(
        "concrete:plates", "concrete"
    )
    return metadata


def write_tiles_within_boundary(csv_path, boundary):
    bbox = boundary.total_bounds

    tiles = list()
    tiles += list(mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], config.zoom))

    with open(csv_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["x", "y", "z", "lat", "lon"])
        for i in range(0, len(tiles)):
            tile = tiles[i]
            lon, lat = tile_center(tile.x, tile.y, config.zoom)
            point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
            # if tile center within boundary of city, write to csv
            if boundary.geometry.contains(point)[0]:
                csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon])


# create cropping frame
def save_image_with_lines(image_path, output_path):
    # Open the image file
    img = Image.open(image_path)
    img_arr = np.array(img)

    fig, ax = plt.subplots()
    ax.imshow(img_arr)

    # Get the dimensions of the image
    height, width, _ = img_arr.shape

    # Calculate the positions of the lines
    middle_horizontal = height // 2
    one_third_vertical = width // 4
    two_thirds_vertical = 3 * width // 4

    # Draw a horizontal line in the middle of the image
    ax.axhline(y=middle_horizontal, color="red", linewidth=2)

    # Draw two vertical lines dividing the image into thirds
    ax.axvline(x=one_third_vertical, color="red", linewidth=2)
    ax.axvline(x=two_thirds_vertical, color="red", linewidth=2)

    # Remove axis
    ax.axis("off")

    # Save the figure to a file
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0, dpi=300)
    plt.close()


def crop_frame_for_img_folder(folder_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all files in the given folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
        ):
            image_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, filename)
            save_image_with_lines(image_path, output_path)
            print(f"Processed {filename}")
