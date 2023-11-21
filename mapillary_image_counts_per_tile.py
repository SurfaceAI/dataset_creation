## create csv with number of mapillary images for each tile in given bounding box

import mercantile
import requests
import csv
from vt2geojson.tools import vt_bytes_to_geojson
import time
import math
import concurrent.futures

# ---------------------

# output path
out_path = 'germany_image_counts.csv'

# Germany Bounding Box
west, south, east, north = [
    5.866240000000001,
    47.27011000000001,
    15.041880000000001,
    54.98310499999999,
]

# ---------------------


# convert tile coordinates to lat/lon
# from: https://wiki.openstreetmap.org/wiki/DE:Slippy_map_tilenames
def num2deg(xtile, ytile, zoom):
  xtile = int(xtile)+0.5 # get center
  ytile = int(ytile)+0.5 # get center
  n = 1 << zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return lat_deg, lon_deg

start = time.time()

# load mapillary access tokens
token_path = 'mapillary_token.txt'
with open(token_path, 'r') as file:
    #access_token = tokenfile.readlines()
    access_tokens = [line.strip() for line in file.readlines()]

current_token = 0

tile_coverage = 'mly1_public'
tile_layer = "image" #"overview"
zoom = 14
# get list of tiles with x and y coordinates which intersect the bounding box
# MUST be at zoom level 14 where the data is available, other zooms currently not supported
tiles = list(mercantile.tiles(west, south, east, north, zoom))
# all of Germany: 
# 235.478 tiles (zoom 14)

def get_tile_number(tile):
    return (tiles.index(tile))

def get_tile_data(tile):
    global current_token
    #print(tile)
    tile_no = get_tile_number(tile)
    print(tile_no)
    # if (tile_no % 5 == 0) or (tile_no % 6 == 0):
    #     print("sleep for 5 seconds")
    #     time.sleep(5) 

    tile_url = 'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}?access_token={}'.format(tile_coverage,tile.z,tile.x,tile.y,access_tokens[current_token])
    response = requests.get(tile_url)

    # if rate limit is reached, try with other access token
    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        current_token = abs(current_token-1) # switch between 0 and 1
        tile_url = 'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}?access_token={}'.format(tile_coverage,tile.z,tile.x,tile.y,access_tokens[current_token])
        response = requests.get(tile_url)
    
    data = vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z,layer=tile_layer)
    return (len(data['features']))

# Number of parallel threads (adjust as needed)
num_threads = 8

with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    # Using executor.map to parallelize the function
    results = list(executor.map(get_tile_data, tiles))

with open(out_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['tilex', 'tiley', 'zoom', 'lat', 'lon', 'image_count'])
    for i in range(0, len(tiles)):
        tile = tiles[i]
        image_count = results[i]
        lat, lon = num2deg(tile.x, tile.y, zoom)
        csvwriter.writerow([tile.x, tile.y, zoom, lat, lon, image_count])

end = time.time()
print(f"{(end - start)/60} minutes")

# 21 minutes for 793 tiles
# 7 minutes for 793 tiles with 4 threads
# 124 minutes for Germany with 8 threads



