import os
import sys
from pathlib import Path
import time

from tqdm import tqdm

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))
sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))

import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

import config
import utils
import database_credentials as db

# create mapillary metadata only for v12

def create_metadata_csv(absolute_path):
    v5path = os.path.join(
            os.getcwd(), config.train_tiles_metadata_path.format("v5")
        )
    metadata = pd.read_csv(v5path, dtype={"id": str})
    print("metadata loaded")
    v5_selection = pd.read_csv("/Users/alexandra/Documents/GitHub/dataset_creation/data/v5/train_image_selection_metadata.csv", dtype={"id": str})
    #v12 = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V12/metadata/annotations_combined.csv", dtype={"image_id": str})
    metadata_v5 = metadata[metadata.id.isin(v5_selection.id)]

    metadata_v5.to_csv(absolute_path, index=False)
    return (absolute_path)


def to_db(absolute_path, name = "v5new"):
    with open(config.sql_script_mapillary_meta_to_database_path, "r") as file:
        query = file.read()

    # create table in postgres for v12 metadata

    # Connect to your PostgreSQL database 
    conn = psycopg2.connect(
        dbname=db.database,
        user=db.user,
        host=db.host,
    )
    # Execute the query
    with conn.cursor(cursor_factory=DictCursor) as cursor:

        cursor.execute(
            sql.SQL(
                query.format(
                    table_name=f"{name}_mapillary_meta",
                    absolute_path=absolute_path,
                )
            )
        )
        conn.commit()
    conn.close()


def intersect_osm(absolute_path, name="v5new"):
    # intersect v12 with osm
    tiles = pd.read_csv(absolute_path)
    tile_ids = tiles.tile_id

    start = time.time()
    print(f"{len(tile_ids.unique())} tiles to intersect with OSM")
    for tile_id in tqdm(tile_ids.unique()):
        utils.intersect_mapillary_osm(tile_id, f"{name}_mapillary_meta")
    end = time.time()
    print(f"{round((end-start) / 60)} mins to intersect all selected test tiles")


if __name__ == "__main__": 
    absolute_path = "/Users/alexandra/Documents/GitHub/dataset_creation/data/v5_mapillary_metadata.csv"
    dest_path = "/Users/alexandra/Documents/GitHub/dataset_creation/data/v5_mapillary_metadata_with_tags_NEW.csv"

    create_metadata_csv(absolute_path)
    to_db(absolute_path)
    intersect_osm(absolute_path)

    utils.save_sql_table_to_csv(
        f"v5new_mapillary_meta",
         dest_path
    )

    