import os
import csv
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
  return lon_deg,lat_deg

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return xtile, ytile

def tile_bbox(xtile, ytile, zoom):
    west, north = num2deg(xtile - 0.5, ytile - 0.5, zoom)
    east, south = num2deg(xtile + 0.5, ytile + 0.5, zoom)
    return west, south, east, north

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
    if response.status_code != 200:
        print(response.status_code)
        print(response.reason)
        print(f"image_id: {image_id}")
    else:
        data = response.json()
        if config.image_size in data:
            image_url = data[config.image_size]

            # image: save each image with ID as filename to directory by sequence ID
            image_name = '{}.jpg'.format(image_id)
            image_path = os.path.join(image_folder, image_name)
            with open(image_path, 'wb') as handler:
                image_data = requests.get(image_url, stream=True).content
                handler.write(image_data)
        else:
            print(f"no image size {config.image_size} for image {image_id}")

def query_and_write_img_metadata(tiles, out_path):
    # write metadata of all potential images to csv
    with open(out_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        for i in range(0, len(tiles)):
            if i % 10 == 0:
                print(f"{i} tiles of {len(tiles)}")
            tile = tiles.iloc[i,]
            header, output = get_tile_metadata(tile)
            if i == 0:
                csvwriter.writerow(header)
            for row in output:
                csvwriter.writerow(row)