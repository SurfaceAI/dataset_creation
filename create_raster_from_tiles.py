import math
import pandas as pd
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
import rpy2.robjects as robjects

#### create a mapbox tile raster template based on dataset with tile coordinates
# create a template raster with empty values
# create a raster with image counts (as given in column *image_count* in the input csv)

# -------------
input_path = 'data/germany_image_counts_old.csv'
template_output_path = 'data/germany_tile_raster_template.tif'
output_path = 'data/germany_tile_raster.tif'

# input_path = 'data/berlin_image_counts.csv'
# template_output_path = 'data/berlin_tile_raster_template.tif'
# output_path = 'data/berlin_tile_raster.tif'
# -------------


# get bounding box of tiles dataset


# function to convert tile coordinates to lat/lon
# from: https://wiki.openstreetmap.org/wiki/DE:Slippy_map_tilenames
def num2deg(xtile, ytile, zoom):
  xtile = int(xtile)
  ytile = int(ytile)
  n = 1 << zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return lon_deg,lat_deg

# function to create a raster template
robjects.r("""
library(terra)
library(sf)
           
create_tile_raster <- function(xmin, xmax, ymin, ymax, nrows, ncols, output_path){

    raster_template <- terra::rast(crs= terra::crs("epsg:3857"), 
                                    xmin = xmin,
                                    xmax= xmax,
                                    ymin= ymin,
                                    ymax= ymax,
                                    ncols = ncols,
                                    nrows = nrows,
                                    vals= 0)

    terra::writeRaster(raster_template, output_path, overwrite=TRUE)
}

rasterize_tiles <- function(raster_path, data_path, output_path){

    raster_template <- terra::rast(raster_path)
    data <- readr::read_csv(data_path)|> 
           st_as_sf( coords = c("lon", "lat"), crs = 4326)|> 
           sf::st_transform(3857)

    raster_template <- terra::rasterize(data, raster_template, field="image_count", fun=max)

    terra::writeRaster(raster_template, output_path, overwrite=TRUE)
}
""")


df = pd.read_csv(input_path)

mins = num2deg(df.tilex.min(), df.tiley.min(), 14)
maxs = num2deg(df.tilex.max()+1, df.tiley.max()+1, 14)

# Create a GeoDataFrame with the min and max points
gdf = gpd.GeoDataFrame(geometry=[Point(mins[0], mins[1]), Point(maxs[0], maxs[1])], crs='EPSG:4326')
# transform crs to web mercator (needed for mapbox tiles)
gdf = gdf.to_crs('EPSG:3857')
xmin = gdf.total_bounds[0]
xmax = gdf.total_bounds[2]
ymin = gdf.total_bounds[1]
ymax = gdf.total_bounds[3]

create_tile_raster_R = robjects.globalenv["create_tile_raster"]
rasterize_tiles_R = robjects.globalenv["rasterize_tiles"]
create_tile_raster_R(int(xmin), int(xmax), int(ymin), int(ymax),
                    len(np.unique(df.tiley)),
                    len(np.unique(df.tilex)),
                    template_output_path)

rasterize_tiles_R(template_output_path, input_path, output_path)