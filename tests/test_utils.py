import pytest
import mercantile

import sys

# setting path
sys.path.append("./")

import utils

def test_tile_center():
    lon_deg, lat_deg = utils.tile_center(8500,5480,14)
    assert lon_deg == 6.778564453125
    assert lat_deg == 51.06211199909443


def test_get_tile_data():
    json = utils.get_tile_data(mercantile.tile(8500,5480,14))
    assert type(json) is dict

def test_get_tile_data():
    pass