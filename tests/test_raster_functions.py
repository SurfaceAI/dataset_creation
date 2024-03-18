import numpy as np
import pandas as pd

import os
import sys

# setting path
sys.path.append("./")

import raster_functions as rf


def test_read_raster():
    raster = rf.read_raster("./tests/test.tif")
    assert type(raster) is np.ndarray


def test_create_raster():
    rf.create_rasterPY(
        0, 1, 0, 1, 4326, "./tests/test_output1.tif", nrows=10, ncols=10
    )
    assert os.path.exists("./tests/test_output1.tif")
    os.remove("./tests/test_output1.tif")

    rf.create_rasterPY(
        0, 1, 0, 1, 4326, "./tests/test_output2.tif", resolution=0.1
    )
    assert os.path.exists("./tests/test_output2.tif")
    os.remove("./tests/test_output2.tif")


def test_raster_to_tiledf():
    df = rf.raster_to_tiledf("./tests/test_tag_counts.tif")
    assert type(df) is pd.DataFrame
    assert sum(df.osmtag_count) == 87930


def test_rasterize_points():
    rf.rasterize_points(
        "./tests/test.tif", "./tests/test_points.csv", 3857, "./tests/test_output.tif"
    )
    assert os.path.exists("./tests/test_output.tif")
    os.remove("./tests/test_output.tif")


def test_raster_ids_for_points():
    rf.raster_ids_for_points(
        "./tests/test.tif", "./tests/test_points.csv", "./tests/test_output.csv", 3857
    )
    assert os.path.exists("./tests/test_output.csv")
    os.remove("./tests/test_output.csv")