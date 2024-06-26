import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))

from ds_creation_steps import s1_select_train_tiles as s1
from ds_creation_steps import s2_get_train_tiles_metadata as s2
from ds_creation_steps import s3_intersect_mapillary_osm as s3
from ds_creation_steps import s4_select_train_images as s4
from ds_creation_steps import s5_download_train_images as s5
from ds_creation_steps import s6_prepare_manual_annotation as s6
from ds_creation_steps import s7_prepare_image_folders as s7

import config
import constants as const

# the selection of images is based on a selection of mercantile tiles (Zoom14).
# First, tiles are selected, then, from within the tiles, images are selected.

## Test data ##
# Step 0: select test cities and create test data
test_cities = [
    const.COLOGNE,
    const.MUNICH,
    const.DRESDEN,
    const.HEILBRONN,
    const.LUNENBURG,
]
# s0.create_test_data(test_cities)

## Training data ##

# Step 1: select training tiles
# test tiles are excluded and diverse tiles according to OSM tags and with minimum mapillary images are selected
if not os.path.exists(config.train_tiles_selection_path.format(config.ds_version)):
    s1.select_train_tiles(test_cities)
else:
    print(
        f"tiles already selected ({config.train_tiles_selection_path.format(config.ds_version)}), step is skipped"
    )

# Step 2: from our selected tiles, get metadata for all images within these training tiles
# takes some time: for ~5400 tiles, ~4h
if not os.path.exists(config.train_tiles_metadata_path.format(config.ds_version)):
    s2.get_train_tiles_metadata()
else:
    print(
        f"tile metadata already queried ({config.train_tiles_metadata_path.format(config.ds_version)}), step is skipped"
    )

# Step 3: intersect all mapillary images (metadata) with OSM data to retrieve respective surface/smoothness/highway tags
# takes some time: for ~4000 tiles, ~16h
if not os.path.exists(
    config.train_image_metadata_with_tags_path.format(config.ds_version)
):
    s3.intersect_mapillary_osm()
else:
    print(
        f"already intersected with OSM {config.train_image_metadata_with_tags_path.format(config.ds_version)}, step is skipped"
    )

# Step 4: filter and select a sample of training images from all images within the selected training tiles that have OSM tags
if not os.path.exists(
    config.train_image_selection_metadata_path.format(config.ds_version)
):
    s4.select_training_sample()
else:
    print(
        f"training images already selected ({config.train_image_selection_metadata_path.format(config.ds_version)}), step is skipped"
    )
s4.create_chunks(config.chunk_ids)

# Step 5: finally, download our selected training images
# download of 5500 images takes ~110 mins
# if not os.path.exists(img_folder):
s5.download_training_images(config.chunk_ids)
# else:
print(f"training images already downloaded, step is skipped")

# Step 6: prepare data for manual labeling with labelstudio
s6.prepare_manual_annotation(config.chunk_ids)

# Step 7: prepare image folders for manual labeling
output_version = "V7"
input_versions = ["V4", "V5_c0", "V5_c1", "V5_c2"]
root_path = os.path.join(
    config.cloud_image_folder,
    "training",
)
s7.create_image_folders(output_version, input_versions, root_path)
