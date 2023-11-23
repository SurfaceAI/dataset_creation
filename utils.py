import math
import mercantile
import config
import requests 
from vt2geojson.tools import vt_bytes_to_geojson

# set access tokens
with open(config.token_path, 'r') as file:
    #access_token = tokenfile.readlines()
    access_tokens = [line.strip() for line in file.readlines()]
current_token = 0

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

def get_mapbox_tiles(west, south, east, north, zoom):
    tiles = list(mercantile.tiles(west, south, east, north, zoom))
    return tiles


'''get tile data from mapillary'''
def get_tile_data(tile):
    global current_token

    response = requests.get(
        'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}'.format(config.tile_coverage,tile.z,tile.x,tile.y),
        params={'access_token': access_tokens[current_token]},
    )

    # if rate limit is reached, try with other access token
    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        current_token = abs(current_token-1) # switch between 0 and 1 and try again
        response = requests.get(
            'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}'.format(config.tile_coverage,tile.z,tile.x,tile.y),
            params={'access_token': access_tokens[current_token]},
        )
    
    # return response
    return vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z,layer=config.tile_layer)