import sys

import mercantile
import pandas as pd

import os
import sys
from pathlib import Path

# setting path
sys.path.append(str(Path(os.path.abspath(__file__)).parent))

import src.utils as utils


def test_tile_center():
    lon_deg, lat_deg = utils.tile_center(8500, 5480, 14)
    assert round(lon_deg, 6) == 6.778564
    assert round(lat_deg, 6) == 51.075919


def test_get_tile_images():
    json = utils.get_tile_images(mercantile.tile(8500, 5480, 14))
    assert type(json) is dict


def test_get_images_metadata():
    header, output = utils.get_images_metadata(mercantile.tile(8500, 5480, 14))
    assert header == [
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
    assert type(output) is list


def test_clean_surface():
    df = pd.DataFrame({"surface": ["asphalt", "cobblestone", "gravel"]})
    df = utils.clean_surface(df)
    assert df.surface_clean.to_list() == ["asphalt", "sett", "unpaved"]
