import os
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
            config.mapillary_tile_url.format(config.tile_coverage,int(tile.z),int(tile.x),int(tile.y)),
            params={'access_token': access_tokens[current_token]},
        )

    # if rate limit is reached, try with other access token
    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        current_token = abs(current_token-1) # switch between 0 and 1 and try again
        response = requests.get(
            config.mapillary_tile_url.format(config.tile_coverage,int(tile.z),int(tile.x),int(tile.y)),
            params={'access_token': access_tokens[current_token]},
        )
    
    # return response
    return vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z,layer=config.tile_layer)


def get_tile_metadata(tile):
    global current_token
    header = ['tile_id', 'id', 'sequence_id', 'captured_at', 'compass_angle', 'is_pano', 'creator_id', 'lon','lat']
    output = list()
    response = requests.get(
                    config.mapillary_tile_url.format(config.tile_coverage,int(tile.z),int(tile.x),int(tile.y)),
                    params={'access_token': access_tokens[current_token]},
            )
    data = vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z,layer=config.tile_layer)
    
    # a feature is a point/image
    # TODO: can this be speed up?
    for feature in data['features']:
        output.append([str(int(tile.x)) + "_" + str(int(tile.y)) + "_" + str(int(tile.z)),
                       feature['properties']['id'], 
                       feature['properties']['sequence_id'], 
                       feature['properties']['captured_at'], 
                       feature['properties']['compass_angle'], 
                       feature['properties']['is_pano'], 
                       feature['properties']['creator_id'], 
                       feature['geometry']['coordinates'][0], 
                       feature['geometry']['coordinates'][1]])
        
    return (header, output)

def download_image(image_id, image_folder):
    header = {'Authorization' : 'OAuth {}'.format(access_tokens[current_token])}
    url = 'https://graph.mapillary.com/{}?fields={}'.format(image_id, config.image_size)
    response = requests.get(url, headers=header)
    data = response.json()
    image_url = data[config.image_size]

    # image: save each image with ID as filename to directory by sequence ID
    image_name = '{}.jpg'.format(image_id)
    image_path = os.path.join(image_folder, image_name)
    with open(image_path, 'wb') as handler:
        image_data = requests.get(image_url, stream=True).content
        handler.write(image_data)