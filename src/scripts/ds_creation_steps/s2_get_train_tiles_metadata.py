import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

import config
import database_credentials as db
import utils as utils


# 3. from these tiles, get metadata
def get_train_tiles_metadata(write_to_db=True):
    tiles = pd.read_csv(config.train_tiles_selection_path.format(config.ds_version))
    utils.query_and_write_img_metadata(
        tiles, config.train_tiles_metadata_path.format(config.ds_version)
    )

    if write_to_db:
        print("write mapillary metadata to database")
        # write metadata to database
        with open(config.sql_script_mapillary_meta_to_database_path, "r") as file:
            query = file.read()

        # Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname=db.database,
            user=db.user,
            host=db.host,
        )
        # Execute the query
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            absolute_path = os.path.join(
                os.getcwd(), config.train_tiles_metadata_path.format(config.ds_version)
            )
            cursor.execute(
                sql.SQL(
                    query.format(
                        table_name=f"{config.ds_version}_mapillary_meta",
                        absolute_path=absolute_path,
                    )
                )
            )
            conn.commit()
        conn.close()


if __name__ == "__main__":
    get_train_tiles_metadata()

    # V200
    get_train_tiles_metadata(write_to_db=False)
