import os
import csv
import mercantile
import config
import requests
from vt2geojson.tools import vt_bytes_to_geojson
import time
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

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
    upperright = mercantile.ul(xtile, ytile, zoom)
    lowerleft =  mercantile.ul(xtile, ytile, zoom)
    lon = (upperleft.lng + upperright.lng) / 2
    lat = (upperleft.lat + lowerleft.lat) / 2
    return lon, lat


def get_tile_data(tile):
    """Get metadata for all images within a tile from mapillary (based on tiles endpoint)
    
    Args:
        tile(mercantile.Tile): mercantile tile

    Returns:
        dict: Metadata of all images within tile as json (dict).
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


def get_tile_metadata(tile):
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
    # write metadata of all potential images to csv
    with open(out_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        for i in range(0, len(tiles)):
            if i % 10 == 0:
                print(f"{i} tiles of {len(tiles)}")
            tile = tiles.iloc[i,]
            header, output = get_tile_metadata(tile)
            if i == 0:
                csvwriter.writerow(header)
            for row in output:
                csvwriter.writerow(row)


def intersect_mapillary_osm(tile_id, table_name):
    start_query = time.time()

    tilex, tiley, zoom = str.split(tile_id, "_")
    bbox = mercantile.bounds(int(tilex), int(tiley), int(zoom))
    with open(config.sql_script_intersect_osm_mapillary_path, "r") as file:
        query = file.read()
        query = str.replace(query, "{table_name}", table_name)

    query = query.format(
        bbox[0], bbox[1], bbox[2], bbox[3], bbox[0], bbox[1], bbox[2], bbox[3]
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

    end_query = time.time()
    # print(f"{tile_id} took {(round(end_query-start_query))} secs for intersection")


def save_sql_table_to_csv(table_name, output_path, where_clause="where highway != ''"):
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
        cursor.execute(sql.SQL(query.format(table_name, where_clause, absolute_path)))
        conn.commit()
    conn.close()
    print("csv exported from db")
