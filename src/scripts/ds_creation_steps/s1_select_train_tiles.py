import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import random
import pandas as pd

import scripts.osm_tag_counts_as_raster as otag
from scripts.mapillary_image_counts_per_tile import mapillary_image_counts_per_tile

import config
import constants as const
import raster_functions as rf


def select_train_tiles(
    exclude_cities,
    use_osm_tags=True,
    tag_combiantions=None,
    remove_old_tiles=True,
    random_state=1,
):
    test_tiles = pd.DataFrame()
    for city in exclude_cities:
        city_tiles = pd.read_csv(config.test_city_tiles_path.format(city))
        test_tiles = pd.concat([test_tiles, city_tiles])

    if not os.path.exists(config.germany_tiles_path):
        print(
            f"Mapillary image counts for germany ({config.germany_tiles_path}) does not exist. Creating it now. This might take a few hours."
        )
        mapillary_image_counts_per_tile(config.germany_tiles_path, const.BBOX_GERMANY)

    tiles = pd.read_csv(config.germany_tiles_path)
    tiles["tile_id"] = (
        tiles["x"].astype(str)
        + "_"
        + tiles["y"].astype(str)
        + "_"
        + tiles["z"].astype(str)
    )
    test_tiles["tile_id"] = (
        test_tiles["x"].astype(str)
        + "_"
        + test_tiles["y"].astype(str)
        + "_"
        + test_tiles["z"].astype(str)
    )
    # keep all tiles except the test city tiles
    tiles = tiles[~tiles["tile_id"].isin(test_tiles["tile_id"])]

    # remove tiles from previous training data
    if remove_old_tiles:
        old_ds_versions = ["v5"]
        for ds_version in old_ds_versions:
            old_tiles = pd.read_csv(
                config.train_tiles_selection_path.format(ds_version)
            )
            old_tiles["tile_id"] = (
                old_tiles["x"].astype(str)
                + "_"
                + old_tiles["y"].astype(str)
                + "_"
                + old_tiles["z"].astype(str)
            )
            tiles = tiles[~tiles["tile_id"].isin(old_tiles["tile_id"])]

    sampled_tiles = pd.DataFrame()

    if use_osm_tags:
        if tag_combiantions is None:
            surfaces = config.surfaces
        else:
            surfaces = tag_combiantions.keys()
        for surface in surfaces:
            if tag_combiantions is None:
                smoothnesses = config.surf_smooth_comb[surface]
            else:
                smoothnesses = tag_combiantions[surface]
            for smoothness in smoothnesses:
                print(f"Sampling tiles for {surface} {smoothness}")
                tif_path = os.path.join(
                    config.tag_counts_path,
                    f"{surface}_{smoothness}_counts_germany.tif",
                )
                if not os.path.exists(tif_path):
                    print(
                        f"OSM tag count tif does not exist for {surface} {smoothness}. Creating it now."
                    )
                    otag.create_osm_tag_count_tif(surface, smoothness)

                # TODO: can we speed this up?
                osm_tiles = rf.raster_to_tiledf(
                    os.path.join(
                        config.tag_counts_path,
                        f"{surface}_{smoothness}_counts_germany.tif",
                    )
                )

                # filter all tiles that have been removed from tiles df (i.e. test cities)
                osm_tiles = osm_tiles[osm_tiles.tile_id.isin(tiles.tile_id)]

                # filter according to minimum number of tags in tiles to only obtain tiles with enough tags
                thres = osm_tiles.osmtag_count[osm_tiles.osmtag_count > 0].quantile(
                    0.75
                )
                osm_tiles = osm_tiles[osm_tiles["osmtag_count"] >= thres]

                # sample tiles for this surface / smoothness combination
                n_tiles = (
                    config.tile_sample_size
                    if config.tile_sample_size < len(osm_tiles)
                    else len(osm_tiles)
                )
                random.seed(1)
                sampled_tile_ids = random.sample(osm_tiles.tile_id.tolist(), n_tiles)
                temp_sampled_tiles = tiles[tiles.tile_id.isin(sampled_tile_ids)].copy()
                temp_sampled_tiles.loc[:, "surface"] = surface
                temp_sampled_tiles.loc[:, "smoothness"] = smoothness
                temp_sampled_tiles = pd.concat(
                    [
                        temp_sampled_tiles.set_index("tile_id"),
                        osm_tiles.set_index("tile_id")["osmtag_count"],
                    ],
                    axis=1,
                    join="inner",
                )

                sampled_tiles = pd.concat([sampled_tiles, temp_sampled_tiles])
    else:
        sampled_tiles = tiles[tiles.image_count > config.min_images].sample(
            config.ds_tile_count, random_state=random_state
        )

    os.makedirs(
        Path(config.train_tiles_selection_path.format(config.ds_version)).parent,
        exist_ok=True,
    )
    sampled_tiles.to_csv(
        config.train_tiles_selection_path.format(config.ds_version), index=False
    )


if __name__ == "__main__":
    test_cities = [
        const.COLOGNE,
        const.MUNICH,
        const.DRESDEN,
        const.HEILBRONN,
        const.LUNENBURG,
    ]

    # select_train_tiles(test_cities)
    # select_train_tiles(test_cities, use_osm_tags=True,
    #                    tag_combiantions={"asphalt": [const.INTERMEDIATE, const.BAD],
    #                                     "concrete": [const.EXCELLENT, const.GOOD, const.INTERMEDIATE, const.BAD],
    #                                     "paving_stones": [const.EXCELLENT, const.INTERMEDIATE, const.BAD],
    #                                     "sett": [const.GOOD, const.BAD],
    #                                     "unpaved": [const.INTERMEDIATE, const.BAD, const.VERY_BAD]})

    # V200
    select_train_tiles(
        test_cities, use_osm_tags=False, remove_old_tiles=False, random_state=123
    )
