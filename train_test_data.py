# Strategy to create test data:
# 1. select test cities 
# Nord: Lüneburg (80.000)
# West: Cologne (1,1 Mio)
# Southeast: bamberg (80.000)
# South: heilbronn (130.000)
# East: dresden (550.000)
# 2. query mapillary tiles and images after year 2022
# 3. select random 10.000 images per 

import os
import time
import csv
import utils
import config
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# store all tiles that cover the test cities in a csv file (#1)
create_test_data = False
create_training_tiles = False

if create_test_data:
    #cities = [config.bbox_luenburg, config.bbox_cologne, config.bbox_bamberg, config.bbox_heilbronn, config.bbox_dresden]
    
    cities = [config.bbox_bamberg]
    boundary = gpd.read_file(config.bamberg_shape, crs="EPSG:4326")

    start = time.time()
    tiles = list()
    for city in cities:
        tiles += utils.get_mapbox_tiles(city[0], city[1], city[2], city[3], config.zoom)
    

    with open(config.test_city_tiles_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['x', 'y', 'z', 'lat', 'lon'])
        for i in range(0, len(tiles)):
            tile = tiles[i]

            lat, lon = utils.num2deg(tile.x, tile.y, config.zoom)
            point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")

            # if tile within boundary of city, write to csv
            if (boundary.geometry.contains(point)[0]):
                csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon])


    
    # 2. query mapillary tiles and images after year 2022
    tiles = pd.read_csv(config.test_city_tiles_path)
    print(len(tiles))
    
    # write metadata of all potential images to csv
    with open(config.test_tiles_metadata_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        for i in range(0, len(tiles)):
            if i % 10 == 0:
                print(f"{i} tiles of {len(tiles)}")
            tile = tiles.iloc[i,]
            header, output = utils.get_tile_metadata(tile)
            if i == 0:
                csvwriter.writerow(header)
            for row in output:
                csvwriter.writerow(row)

    # filter by year
    metadata = pd.read_csv(config.test_tiles_metadata_path)
    # only images after defined timestamp
    metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]

    # TODO: should we remove the bias many samples from roads with many images?
    # take max 5 images per sequence
    # take max 150 images per tile
    # 3. select random x images per city
    metadata = (metadata
                .groupby("sequence_id")
                .sample(config.max_img_per_sequence, random_state=1, replace=True,)
                .groupby("tile_id")
                .sample(config.max_img_per_tile, random_state=1, replace=True,)
                .drop_duplicates()
                .sample(1000, random_state=1))

    metadata.to_csv(config.test_image_selection_metadata_path, index=False)

# download images

start = time.time()

if not os.path.exists(config.test_image_folder):
    os.makedirs(config.test_image_folder)
    
with open(config.test_image_selection_metadata_path, newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    image_ids = [row[1] for row in csvreader][1:]
    for i in range(0, len(image_ids)):
        if i % 100 == 0:
            print(f"{i} images downloaded")
        utils.download_image(image_ids[i], config.test_image_folder)

print(f"{round(time.time()-start)} seconds")


##########################################


# Strategy to create training data:
# 1. filter suitable tiles:
#   - exclude all tiles of test data cities
#   - remove those with images < x 
#   - remove those with surface / smoothness tag count < y
#   - from these tiles, select x random tiles
# 2. to make sure, surface / smoothness combinations are all represented, select top 10 tiles for each combination 
# 3. from these tiles, get metadata. filter images after year 2022. Only select one random image from each sequence
# 4. get OSM data for these tiles and filter roads with surface / smoothness info and buffer around suitable ways
#    - check type of road (primary, secondary, tertiary, residential, unclassified, service, track) 
# 5. intersect datasets and check if each surface / smoothness combination reaches at least 1500 images
# - if not, sample more tiles
# 6. for combinations with more than 1500 images, sample 1500 images
# 7. then download images

##1 filter suitable tiles


if create_training_tiles:
    tiles = pd.read_csv(config.germany_tiles_path)

    print(len(tiles))
    #   - exclude all tiles of test data cities
    test_tiles = pd.read_csv(config.test_city_tiles_path)
    tiles["tile_id"] = tiles["x"].astype(str) + "_" + tiles["y"].astype(str) + "_" + tiles["z"].astype(str)
    test_tiles["tile_id"] = test_tiles["x"].astype(str) + "_" + test_tiles["y"].astype(str) + "_" + test_tiles["z"].astype(str)
    tiles = tiles[~tiles["tile_id"].isin(test_tiles["tile_id"])]
    print(len(tiles))

    #   - remove those with images < x 
    tiles = tiles[tiles["image_count"] >= 1000]
    tiles = tiles[tiles["is_pano"] is False]

    #   - remove those with surface / smoothness tag count < y
    # TODO

    #   - from these tiles, select x random tiles
    tiles = tiles.sample(1000, random_state=1)

    ## 2 to make sure, surface / smoothness combinations are all represented, select top 10 tiles for each combination 


    # 3. from these tiles, get metadata
    tile_metadata = list()
    for i in range(0, len(tiles)):
        if i % 100 == 0:
            print(f"{i} tiles of {len(tiles)}")
        tile = tiles.iloc[i]
        tile_metadata += utils.get_tile_metadata(tile)

    # write metadata of all potential images to csv
    with open(config.train_tiles_metadata_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        for i in range(0, len(tile_metadata)):
            tile = tile_metadata[i]
            csvwriter.writerow(tile)

    # filter images after year 2022. Only select one random image from each sequence