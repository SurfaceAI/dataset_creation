import os
import time
import csv
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import sys

# setting path
sys.path.append("./")
sys.path.append("../")

import utils
import config
import constants as const
import raster_functions as rf
import database_credentials as db


def get_autonahn_in_boundary(city, boundary):
    # filter out images on the autobahn
    if os.path.exists(config.filtered_autobahn_path.format(city)):
        autobahn_in_boundary = gpd.read_file(
            config.filtered_autobahn_path.format(city), crs="EPSG:3035"
        )
    else:
        autobahn = gpd.read_file(config.autobahn_path, crs="EPSG:3035").to_crs(
            "EPSG:3035"
        )
        autobahn_in_boundary = autobahn[
            autobahn.intersects(boundary.geometry.to_crs(3035)[0])
        ]
        autobahn_in_boundary.to_file(
            config.filtered_autobahn_path.format(city), driver="GeoJSON"
        )
    return autobahn_in_boundary


def select_test_images(city, boundary, center_bbox):
    metadata = pd.read_csv(config.test_tiles_metadata_path.format(city), dtype={"id": int})

    # remove panorama img
    metadata = metadata[metadata["is_pano"] == False]

    # only images after defined timestamp
    metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]
    
    # to get max diversity of images:
    # take max 5 images per sequence
    # take max 5 images per 100 meter raster cell
    # then, select random x images per city
    metadata = (
        metadata.groupby("sequence_id")
        .sample(
            config.max_img_per_sequence_test,
            random_state=1,
            replace=True,
        )
        .groupby("cell_ids")
        .sample(
            config.max_img_per_cell,
            random_state=1,
            replace=True,
        )
        .drop_duplicates()
        .sample(2000, random_state=1)
    )

    # remove images on the autobahn
    autobahn_in_boundary = get_autonahn_in_boundary(city, boundary)


    pts = gpd.GeoDataFrame(
        metadata,
        geometry=[
            Point(lon, lat)
            for lon, lat in zip(metadata["lon"], metadata["lat"])
        ],
        crs="EPSG:4326",
    )
    pts = pts.to_crs("EPSG:3035")
    metadata = metadata[
        ~pts.geometry.intersects(autobahn_in_boundary.unary_union)
    ]

    # select only images from city center
    metadata = metadata[(metadata.lon > center_bbox["xmin"]) & 
                        (metadata.lon < center_bbox["xmax"]) & 
                        (metadata.lat > center_bbox["ymin"]) & 
                        (metadata.lat < center_bbox["ymax"])]

    # sample remaining
    metadata = metadata.sample(config.sample_size_test_city, random_state=1)

    metadata.to_csv(
        config.test_image_selection_metadata_path.format(city), index=False
    )


def download_test_images(city):
    start = time.time()
    os.makedirs(config.test_image_folder.format(city))

    with open(
        config.test_image_selection_metadata_path.format(city), newline=""
    ) as csvfile:
        csvreader = csv.reader(csvfile)
        image_ids = [row[1] for row in csvreader][1:]
        for i in range(0, len(image_ids)):
            if i % 100 == 0:
                print(f"{i} images downloaded")
            utils.download_image(
                int(image_ids[i]), config.test_image_folder.format(city)
            )

    print(f"{round((time.time()-start )/ 60)} mins")


def intersect_test_images_with_osm(city):
    with open(config.sql_script_mapillary_meta_to_database_path, "r") as file:
        query = file.read()

    # Connect to your PostgreSQL database
    conn = psycopg2.connect(
        dbname=db.database,
        user=db.user,
        host=db.host,
    )

    # Execute the intersection query
    temp_path = "data/temp.csv"
    pd.read_csv(config.test_image_selection_metadata_path.format(city)).drop(
        columns=["cell_ids"]
    ).to_csv(temp_path, index=False)

    absolute_path = os.path.join(os.getcwd(), temp_path)
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        query = str.replace(query, "{table_name}", "mapillary_testdata_meta")
        cursor.execute(sql.SQL(query.format(absolute_path)))
        conn.commit()
    conn.close()
    os.remove(absolute_path)

    # for each tile, SQL query of intersecting ways with surface / smoothness tags
    tiles = pd.DataFrame()
    # for city in cities:
    # city_tiles = pd.read_csv(config.test_city_tiles_path.format(city))
    # tiles = pd.concat([tiles, city_tiles]
    tiles = pd.read_csv(config.test_city_tiles_path.format(city))
    tile_ids = (
        tiles["x"].astype(str)
        + "_"
        + tiles["y"].astype(str)
        + "_"
        + tiles["z"].astype(str)
    )

    start = time.time()
    print(f"{len(tile_ids.unique())} tiles to intersect with OSM")
    for tile_id in tile_ids.unique():
        utils.intersect_mapillary_osm(tile_id, "mapillary_testdata_meta")

    end = time.time()
    print(
        f"{round((end-start) / 60)} mins to intersect all selected test tiles"
    )

    utils.save_sql_table_to_csv(
        "mapillary_testdata_meta",
        config.test_image_metadata_with_tags_path.format(city),
        where_clause="",
    )


# def create_test_data(cities):
#     print("create test data")
#     for city in cities:
#         print("city: ", city)

#         boundary = gpd.read_file(config.boundary.format(city), crs="EPSG:4326")

#         # Step 0_0: get all tiles within city boundary and write to csv
#         if not os.path.exists(config.test_city_tiles_path.format(city)):
#              utils.write_tiles_within_boundary(config.test_city_tiles_path.format(city), boundary)
#         else:
#             print(
#                 f"tiles info already downloaded ({config.test_city_tiles_path.format(city)}), step is skipped"
#             )

#         # Step 0_1: get metadata for all images within city boundary
#         tiles = pd.read_csv(config.test_city_tiles_path.format(city))
#         if not os.path.exists(config.test_tiles_metadata_path.format(city)):
#             print(f"download metadata for {len(tiles)} tiles")
#             # write metadata of all potential images to csv
#             utils.query_and_write_img_metadata(
#                 tiles, config.test_tiles_metadata_path.format(city)
#             )
#         else:
#             print(
#                 f"img metadata already downloaded ({config.test_tiles_metadata_path.format(city)}), step is skipped"
#             )

#         # Step 0_2: create samll raster template for city
#         if not os.path.exists(config.test_small_raster_template.format(city)):
#             # create an assignment to a fine grid
#             gdf = gpd.read_file(config.boundary.format(city), crs="EPSG:4326")
#             # transform crs to web mercator (needed for mercantile tiles)
#             gdf = gdf.to_crs("EPSG:3035")
#             xmin, ymin, xmax, ymax = gdf.total_bounds
#             rf.create_raster(
#                 int(xmin),
#                 int(xmax),
#                 int(ymin),
#                 int(ymax),
#                 "epsg:3035",
#                 config.test_small_raster_template.format(city),
#                 resolution=100,
#             )

#             rf.raster_ids_for_points(
#                 config.test_small_raster_template.format(city),
#                 config.test_tiles_metadata_path.format(city),
#                 config.test_tiles_metadata_path.format(city),
#                 3035,
#             )
#         else:
#             print(
#                 f"small raster template already created ({config.test_small_raster_template.format(city)}), step is skipped"
#             )

#         # Step 0_3: select images for test data
#         if not os.path.exists(config.test_image_selection_metadata_path.format(city)):
#             # filter by year
#             select_test_images(city, boundary)
#         else:
#             print(
#                 f"images already selected ({config.test_image_selection_metadata_path.format(city)}), step is skipped"
#             )

#         # Step 0_4: download selected test images
#         if not os.path.exists(config.test_image_folder.format(city)):
#             download_test_images(city)
#         else:
#             print("images already downloaded, step is skipped")

#         # Step 0_5: intersect with OSM
#         if not os.path.exists(config.test_image_metadata_with_tags_path.format(city)):
#             # create mapillary_testdata_meta table in postgres
#             intersect_test_images_with_osm(city)
#         else:
#             print("already intersected with osm, step is skipped")


def raster_id_by_res(boundary, resolution, output_file_path, city):
    # transform crs to web mercator (needed for mercantile tiles)
    boundary = boundary.to_crs("EPSG:3035")
    xmin, ymin, xmax, ymax = boundary.total_bounds
    rf.create_raster(
        int(xmin),
        int(xmax),
        int(ymin),
        int(ymax),
        "epsg:3035",
        output_file_path,
        resolution=resolution,
    )

    rf.raster_ids_for_points(
        config.test_small_raster_template.format(city),
        config.test_tiles_metadata_path.format(city),
        config.test_tiles_metadata_path.format(city),
        3035,
    )


if __name__ == "__main__":
    cities = [
        #const.COLOGNE,
        #const.MUNICH,
        const.DRESDEN,
        #const.HEILBRONN,
        #const.LUNENBURG,
    ]

    for city in cities:
        print("city: ", city)
        boundary = gpd.read_file(config.boundary.format(city), crs="EPSG:4326")
    
        # Step 0_0: get all tiles within city boundary and write to csv
        #utils.write_tiles_within_boundary(config.test_city_tiles_path.format(city), boundary)
    
        # Step 0_1: get metadata for all images within city boundary
        #tiles = pd.read_csv(config.test_city_tiles_path.format(city))
        #utils.query_and_write_img_metadata(
        #    tiles, config.test_tiles_metadata_path.format(city)
        #)
    
        # Step 0_2: create samll raster template for city
        #raster_id_by_res(boundary, 100, config.test_small_raster_template.format(city), city)

        # Step 0_3: select images for test data
        select_test_images(city, boundary, config.center_bboxes[city])

        # Step 0_4: download selected test images
        download_test_images(city)

        # Step 0_5: intersect with OSM
        intersect_test_images_with_osm(city)
