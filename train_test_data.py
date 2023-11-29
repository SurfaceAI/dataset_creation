# Strategy to create test data:
# 1. select test cities 
# Nord: Lüneburg (80.000)
# West: Cologne (1,1 Mio)
# Southeast: bamberg (80.000)
# South: heilbronn (130.000)
# East: dresden (550.000)
# 2. query mapillary tiles and images after year 06.2021
# 3. select random 1.000 images per 

import os
import time
import csv
import utils
import config
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import raster_functions as rf

# store all tiles that cover the test cities in a csv file (#1)

    
def create_test_data(cities):
    print("create test data")
    for city in cities:
        
        print("city: ", city)

        boundary = gpd.read_file(config.boundary.format(city), crs="EPSG:4326")
        bbox = boundary.total_bounds

        ### download all tile metadata
        if not os.path.exists(config.test_city_tiles_path.format(city)):
            tiles = list()
            tiles += utils.get_mapbox_tiles(bbox[0], bbox[1], bbox[2], bbox[3], config.zoom)

            with open(config.test_city_tiles_path.format(city), 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(['x', 'y', 'z', 'lat', 'lon'])
                for i in range(0, len(tiles)):
                    tile = tiles[i]
                    lon, lat = utils.num2deg(tile.x, tile.y, config.zoom)
                    point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
                    # if tile center within boundary of city, write to csv
                    if (boundary.geometry.contains(point)[0]):
                        csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon])
        else:
            print(f"tiles info already downloaded ({config.test_city_tiles_path.format(city)}), step is skipped")



        tiles = pd.read_csv(config.test_city_tiles_path.format(city))

        if not os.path.exists(config.test_tiles_metadata_path.format(city)):
            print(f"download metadata for {len(tiles)} tiles")
            # write metadata of all potential images to csv
            utils.query_and_write_img_metadata(tiles, config.test_tiles_metadata_path.format(city))
        else:
            print(f"img metadata already downloaded ({config.test_tiles_metadata_path.format(city)}), step is skipped")


        if not os.path.exists(config.test_small_raster_template.format(city)):
            # create an assignment to a fine grid
            gdf = gpd.read_file(config.boundary.format(city), crs="EPSG:4326")
            # transform crs to web mercator (needed for mapbox tiles)
            gdf = gdf.to_crs('EPSG:3035')
            xmin, ymin, xmax, ymax = gdf.total_bounds
            rf.create_raster(int(xmin), int(xmax), int(ymin), int(ymax), "epsg:3035", 
                             config.test_small_raster_template.format(city), resolution=100)
            # rf.rasterize_points(config.test_small_raster_template, 
            #                     config.test_tiles_metadata_path, 
            #                     3035, 
            #                     config.test_small_raster_counts, 
            #                     "sum")

            rf.raster_ids_for_points(config.test_small_raster_template.format(city), 
                                    config.test_tiles_metadata_path.format(city), 
                                    config.test_tiles_metadata_path.format(city),  
                                    3035)
        else:
            print(f"small raster template already created ({config.test_small_raster_template.format(city)}), step is skipped")


        if not os.path.exists(config.test_image_selection_metadata_path.format(city)):
            # filter by year
            metadata = pd.read_csv(config.test_tiles_metadata_path.format(city), dtype={"id":int})
            
            # remove panorama img
            metadata = metadata[metadata["is_pano"] == False]

            # only images after defined timestamp
            metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]
            # to get max diversity of images:
            # take max 5 images per sequence
            # take max 5 images per 100 meter raster cell
            # then, select random x images per city
            metadata = (metadata
                        .groupby("sequence_id")
                        .sample(config.max_img_per_sequence_test, random_state=1, replace=True,)
                        .groupby("cell_ids")
                        .sample(config.max_img_per_cell, random_state=1, replace=True,)
                        .drop_duplicates()
                        .sample(2000, random_state=1))
            
            # filter out images on the autobahn
            if (os.path.exists(config.filtered_autobahn_path.format(city))):
                autobahn_in_boundary = gpd.read_file(config.filtered_autobahn_path.format(city), crs="EPSG:3035")
            else:
                autobahn = gpd.read_file(config.autobahn_path, crs="EPSG:3035").to_crs("EPSG:3035")
                autobahn_in_boundary = autobahn[autobahn.intersects(boundary.geometry.to_crs(3035)[0])]
                autobahn_in_boundary.to_file(config.filtered_autobahn_path.format(city), driver='GeoJSON')

            pts = gpd.GeoDataFrame(metadata, geometry=[Point(lon, lat) for lon, lat in zip(metadata['lon'], metadata['lat'])], crs="EPSG:4326")
            pts = pts.to_crs("EPSG:3035")
            metadata = metadata[~pts.geometry.intersects(autobahn_in_boundary.unary_union)]

            # sample 1000 from remaining
            metadata = metadata.sample(1000, random_state=1)

            metadata.to_csv(config.test_image_selection_metadata_path.format(city), index=False)
        else:
            print(f"images already selected ({config.test_image_selection_metadata_path.format(city)}), step is skipped")

        ### download images
        if not os.path.exists(config.test_image_folder.format(city)):
            start = time.time()
            os.makedirs(config.test_image_folder.format(city))
                
            with open(config.test_image_selection_metadata_path.format(city), newline='') as csvfile:
                csvreader = csv.reader(csvfile)
                image_ids = [row[1] for row in csvreader][1:]
                for i in range(0, len(image_ids)):
                    if i % 100 == 0:
                        print(f"{i} images downloaded")
                    utils.download_image(int(image_ids[i]), config.test_image_folder.format(city))

            print(f"{round((time.time()-start )/ 60)} mins")
        else:
            print("images already downloaded, step is skipped")



        ##########################################

# Strategy to create training data:
# 1. filter suitable tiles:
#   - exclude all tiles of test data cities
#   - remove those with images < x 
#   - remove those with surface / smoothness tag count < y
#   - from these tiles, select x random tiles
# 3. from these tiles, get metadata. filter images after year 2022. Only select one random image from each sequence
# 2. to make sure, surface / smoothness combinations are all represented, select top 10 tiles for each combination 
# 4. get OSM data for these tiles and filter roads with surface / smoothness info and buffer around suitable ways
#    - check type of road (primary, secondary, tertiary, residential, unclassified, service, track) 
# 5. intersect datasets and check if each surface / smoothness combination reaches at least 1500 images
# - if not, sample more tiles
# 6. for combinations with more than 1500 images, sample 1500 images
# 7. then download images


def create_training_data(cities):

    #   - exclude all tiles of test data cities
    
    if not os.path.exists(config.train_tiles_selection_path):
        test_tiles = pd.DataFrame()
        for city in cities:
            city_tiles = pd.read_csv(config.test_city_tiles_path.format(city))
            test_tiles = pd.concat([test_tiles, city_tiles])

        tiles = pd.read_csv(config.germany_tiles_path)
        tiles["tile_id"] = tiles["x"].astype(str) + "_" + tiles["y"].astype(str) + "_" + tiles["z"].astype(str)
        test_tiles["tile_id"] = test_tiles["x"].astype(str) + "_" + test_tiles["y"].astype(str) + "_" + test_tiles["z"].astype(str)
        tiles = tiles[~tiles["tile_id"].isin(test_tiles["tile_id"])]


        #mapillary_counts = rf.read_raster(config.germany_raster_image_counts)
        #   - remove those with surface / smoothness tag count < y
        #osm_tags = rf.read_raster(config.germany_osmtag_counts)
        osm_tiles = rf.raster_to_tiledf(config.germany_osmtag_counts)

        tiles = pd.concat([tiles.set_index('tile_id'), osm_tiles.set_index('tile_id')["osmtag_count"]], axis=1, join='inner')

        #   - remove those with images < x 
        tiles = tiles[tiles["image_count"] >= config.min_images]
        tiles = tiles[tiles["is_pano"] == False]
        tiles = tiles[tiles["osmtag_count"] >= config.min_tags]

        #   - from these tiles, select x random tiles
        tiles = tiles.sample(1000, random_state=1)
        tiles.to_csv(config.train_tiles_selection_path, index=False)
    else:
        print(f"tiles already selected ({config.train_tiles_selection_path}), step is skipped")

    # 3. from these tiles, get metadata
    if not os.path.exists(config.train_tiles_metadata_path):
        tiles = pd.read_csv(config.train_tiles_selection_path)
        utils.query_and_write_img_metadata(tiles, config.train_tiles_metadata_path)
    else:
        print(f"tile metadata already queried ({config.train_tiles_metadata_path}), step is skipped")

    if not os.path.exists(config.train_image_selection_metadata_path):
        # 4. filtering
        metadata = pd.read_csv(config.train_tiles_metadata_path, dtype={"id":int})
        # about 10 mio images in 1000 selected tiles

        # filter images after year 2022. 
        metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]
        # 4.602.584 images after 1.6.2021
        print(f"img count after sampling by date {len(metadata)}")
        
        # Only select one random image from each sequence
        metadata = (metadata
                    .groupby("sequence_id")
                    .sample(config.max_img_per_sequence_training, random_state=1, replace=True,))
        # 44.733 sequences
        print(f"img count after sampling by sequence_id {len(metadata)}")

        metadata.to_csv(config.train_image_selection_metadata_path, index=False)
    else:
        print(f"metadata of selected images already queried ({config.train_image_selection_metadata_path}), step is skipped")

        ## 2 to make sure, surface / smoothness combinations are all represented, select top 10 tiles for each combination 


if __name__ == "__main__":

    cities = ["dresden"]
    create_test_data(cities)
    #cities = ["cologne", "muenchen", "dresden", "heilbronn", "lueneburg"]
    #create_training_data(cities)