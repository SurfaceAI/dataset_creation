import pandas as pd
import geopandas as gpd
import raster_functions as rf
import config

gdf = gpd.read_file(config.bamberg_shape, crs="EPSG:4326")
# transform crs to web mercator (needed for mapbox tiles)
gdf = gdf.to_crs('EPSG:3035')
xmin = gdf.total_bounds[0]
xmax = gdf.total_bounds[2]
ymin = gdf.total_bounds[1]
ymax = gdf.total_bounds[3]

rf.create_raster(int(xmin), int(xmax), int(ymin), int(ymax), "epsg:3035", config.test_small_raster_template, resolution=100)
# rf.rasterize_points(config.test_small_raster_template, 
#                     config.test_tiles_metadata_path, 
#                     3035, 
#                     config.test_small_raster_counts, 
#                     "sum")

rf.raster_ids_for_points(config.test_small_raster_template, 
                         config.test_tiles_metadata_path, 
                         config.test_tiles_metadata_path, 
                         3035)