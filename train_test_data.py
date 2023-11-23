# Strategy to create test data:
# 1. select test cities 
# Nord: Lüneburg (80.000)
# West: Cologne (1,1 Mio)
# Southeast: bamberg (80.000)
# South: heilbronn (130.000)
# East: dresden (550.000)
# 2. query mapillary tiles and images after year 2022
# 3. select random 10.000 images per 

# store all tiles that cover the test cities in a csv file (#1)

import time
import csv
import utils
import config

cities = [config.bbox_luenburg, config.bbox_cologne, config.bbox_bamberg, config.bbox_heilbronn, config.bbox_dresden]

start = time.time()
tiles = list()
for city in cities:
    tiles += utils.get_mapbox_tiles(city[0], city[1], city[2], city[3], config.zoom)

with open(config.test_city_tiles_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['tilex', 'tiley', 'zoom', 'lat', 'lon'])
    for i in range(0, len(tiles)):
        tile = tiles[i]
        lat, lon = utils.num2deg(tile.x, tile.y, config.zoom)
        csvwriter.writerow([tile.x, tile.y, config.zoom, lat, lon])


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
