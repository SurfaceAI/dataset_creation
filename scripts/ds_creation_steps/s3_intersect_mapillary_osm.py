import time

import numpy as np
import pandas as pd

import sys

# setting path
sys.path.append("./")
sys.path.append("../")

import utils
import config

def intersect_mapillary_osm():
        # for each tile, SQL query of intersecting ways with surface / smoothness tags
        tiles = pd.read_csv(
            config.train_tiles_selection_path.format(config.ds_version)
        )
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
            if (np.where(tile_ids.unique() == tile_id)[0][0] % 10) == 0:
                print(np.where(tile_ids.unique() == tile_id)[0][0])

            utils.intersect_mapillary_osm(tile_id, "mapillary_meta")

        end = time.time()
        print(f"{round((end-start) / 60)} mins to intersect all selected test tiles")

        utils.save_sql_table_to_csv(
            "mapillary_meta",
            config.train_image_metadata_with_tags_path.format(config.ds_version),
        )

if __name__ == "__main__":
    intersect_mapillary_osm()