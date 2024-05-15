import os
import sys
from pathlib import Path


sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

from tqdm import tqdm
import pandas as pd

import utils as utils
import config

###### use metadata pool of v5 to get more images for v5x #####

# get all metadata from v5
metadata = pd.read_csv(
    config.train_image_metadata_with_tags_path.format("v5"), dtype={"id": str}
)

# drop potential duplicates
metadata.drop_duplicates(subset="id", inplace=True)
metadata = utils.clean_surface(metadata)
metadata = utils.clean_smoothness(metadata)
cleaned_metadata = pd.DataFrame()
for surface in config.surfaces:
    cleaned_metadata = pd.concat(
        [
            cleaned_metadata,
            metadata[
                (
                    (metadata["surface_clean"] == surface)
                    & (
                        metadata["smoothness_clean"].isin(
                            config.surf_smooth_comb[surface]
                        )
                    )
                )
            ],
        ]
    )
metadata = cleaned_metadata


metadata_v5selection = pd.read_csv(
    config.train_image_selection_metadata_path.format("v5")
)

# remove all images that have already been labeled from data pool
with open(config.labeled_imgids_path, "r") as file:
    already_labled_ids = file.read().splitlines()
metadata = metadata[~metadata["id"].isin(already_labled_ids)]
# this is actually redundant, but just to make sure
metadata = metadata[~metadata["id"].isin(metadata_v5selection["id"])]


# for each surface/smoothness combination,
# filter such that only images up to 5 for each sequence and tile remain
metadata_v5x_selection = pd.DataFrame()
for surface in config.surfaces:
    for smoothness in config.surf_smooth_comb[surface]:
        print(f"Surface: {surface}, Smoothness: {smoothness}")

        # gather all "used" tile ids and sequence_ids from v5
        metadata_v5selection_class = metadata_v5selection.loc[
            (
                (metadata_v5selection["surface_clean"] == surface)
                & (metadata_v5selection["smoothness_clean"] == smoothness)
            )
        ]
        sequence_ids = metadata_v5selection_class.groupby("sequence_id").size()
        tile_ids = metadata_v5selection_class.groupby("tile_id").size()

        metadata_class = metadata.loc[
            (
                (metadata["surface_clean"] == surface)
                & (metadata["smoothness_clean"] == smoothness)
            )
        ]

        # sample by sequence_id and tile_id
        sequence_selection = pd.DataFrame()
        for sequence_id in tqdm(sequence_ids.index):
            # how many new images from this sequence_id should be sampled?
            n_to_sample = 5 - sequence_ids[sequence_id]
            n_to_sample = (
                n_to_sample
                if n_to_sample
                <= len(metadata_class[metadata_class.sequence_id == sequence_id])
                else len(metadata_class[metadata_class.sequence_id == sequence_id])
            )

            if n_to_sample < 0:
                print(f"Sequence {sequence_id} already has more than 5 images")
            else:
                temp = metadata_class[metadata_class.sequence_id == sequence_id].sample(
                    n_to_sample, random_state=1
                )
                sequence_selection = pd.concat([sequence_selection, temp])

        for tile_id in tqdm(tile_ids.index):
            # how many new images from this tile_id should be sampled?
            n_to_sample = 5 - tile_ids[tile_id]
            n_to_sample = (
                n_to_sample
                if n_to_sample
                <= len(sequence_selection[sequence_selection.tile_id == tile_id])
                else len(sequence_selection[sequence_selection.tile_id == tile_id])
            )
            temp = (
                sequence_selection[sequence_selection.tile_id == tile_id]
                .groupby(
                    ["tile_id", "surface_clean", "smoothness_clean"]
                )  # restrict number of images per tile (per class)
                .sample(n_to_sample, random_state=1)
            )
            metadata_v5x_selection = pd.concat([metadata_v5x_selection, temp])

metadata_v5x_selection.to_csv(
    config.train_image_selection_metadata_path.format("v5x"), index=False
)
