import os
import sys
from pathlib import Path
sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import config

import pandas as pd

#### query metadata of x random tiles (at least x images per tile) ###
# > s1

# sample 20.000 images
    # - 20 per tile and 
    # - 10 per sequence
    # - exclude all images
    # get all metadata from v5
metadata = pd.read_csv(
    config.train_tiles_metadata_path.format("v200"), dtype={"id": str})

# drop potential duplicates
metadata.drop_duplicates(subset="id", inplace=True)

# remove panorama images
metadata = metadata[metadata["is_pano"] == False]

metadata_v5selection = pd.read_csv(config.train_image_selection_metadata_path.format("v5"))

# remove all images that have already been labeled from data pool
with open(config.labeled_imgids_path, "r") as file:
    already_labled_ids = file.read().splitlines()
metadata = metadata[~metadata["id"].isin(already_labled_ids)]
# this is actually redundant, but just to make sure
metadata = metadata[~metadata["id"].isin(metadata_v5selection["id"])]

# remove all sequence IDs that have already been labeled
metadata = metadata[~metadata["sequence_id"].isin(metadata_v5selection["sequence_id"])]
sample = (metadata
    .groupby("sequence_id")
    .sample(10, random_state=1, replace=True)
    .drop_duplicates(subset="id")
    .groupby("tile_id")
    .sample(20, random_state=1, replace=True)
    .drop_duplicates(subset="id")
    .sample(20_000, random_state=1)
)
sample.to_csv(config.train_image_selection_metadata_path.format("v200"), index=False)