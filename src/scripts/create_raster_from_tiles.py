# setting path
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import raster_functions as rf
import utils as utils

#### create a mercantile tile raster template based on dataset with tile coordinates
# create a template raster with empty values
# create a raster with image counts (as given in column *image_count* in the input csv)

# -------------
# input_path = config.germany_tiles_path
# template_output_path = config.germany_raster_template
# output_path = config.germany_raster_image_counts

input_path = "data/berlin_image_counts.csv"
template_output_path = "data/berlin_tile_raster_template.tif"
output_path = "data/berlin_tile_raster.tif"
# -------------

df = pd.read_csv(input_path)

mins = utils.tile_center(df.x.min(), df.y.min(), 14)
maxs = utils.tile_center(df.x.max() + 1, df.y.max() + 1, 14)

# Create a GeoDataFrame with the min and max points
gdf = gpd.GeoDataFrame(
    geometry=[Point(mins[0], mins[1]), Point(maxs[0], maxs[1])], crs="EPSG:4326"
)
# transform crs to web mercator (needed for mercantile tiles)
gdf = gdf.to_crs("EPSG:3857")
xmin = gdf.total_bounds[0]
xmax = gdf.total_bounds[2]
ymin = gdf.total_bounds[1]
ymax = gdf.total_bounds[3]

# create_raster_R = robjects.globalenv["create_raster"]
# rasterize_points_R = robjects.globalenv["rasterize_points"]
rf.create_raster(
    int(xmin),
    int(xmax),
    int(ymin),
    int(ymax),
    "epsg:3857",
    template_output_path,
    nrows=len(np.unique(df.y)),
    ncols=len(np.unique(df.x)),
)

rf.rasterize_points(template_output_path, input_path, 3857, output_path, "max")
