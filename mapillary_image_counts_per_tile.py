## create csv with number of mapillary images for each tile in given bounding box

import mercantile
import requests
import csv
from vt2geojson.tools import vt_bytes_to_geojson
import time
import math
import concurrent.futures
import config
import utils

# ---------------------

# output path
out_path = config.germany_tiles_path
bbox = config.bbox_germany

out_path = "test_bamberg.csv"
bbox = config.bbox_bamberg

# ---------------------


start = time.time()

tiles = utils.get_mapbox_tiles(bbox[0], bbox[1], bbox[2], bbox[3], config.zoom)

current_token = 0

def get_tile_number(tile):
    return (tiles.index(tile))

def counts_per_tile(tile):
    global current_token
    #print(tile)
    tile_no = get_tile_number(tile)
    print(tile_no)

    data = utils.get_tile_data(tile)
    return (len(data['features']))

# Number of parallel threads (adjust as needed)
num_threads = 8

with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    # Using executor.map to parallelize the function
    results = list(executor.map(counts_per_tile, tiles))

with open(out_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['tilex', 'tiley', 'zoom', 'lat', 'lon', 'image_count'])
    for i in range(0, len(tiles)):
        tile = tiles[i]
        image_count = results[i]
        lat, lon = utils.num2deg(tile.x, tile.y, config.zoom)
        csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon, image_count])

end = time.time()
print(f"{(end - start)/60} minutes")

# 21 minutes for 793 tiles
# 7 minutes for 793 tiles with 4 threads
# 293 minutes (ca. 5h) for Germany (235.478 tiles) with 8 threads



