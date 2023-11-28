germany_tiles_path = 'data/germany_image_counts.csv'
germany_raster_template = 'data/germany_tile_raster_template.tif'
germany_raster_image_counts = 'data/germany_mapillary_counts_raster.tif'
germany_osmtag_counts = 'data/germany_osmtag_counts.tif'
autobahn_path = 'data/autobahn.shp'
filtered_autobahn_path = 'data/{}/autobahn_filtered.geojson'
# berlin_tiles_path = 'data/berlin_image_counts.csv'
# berlin_raster_template = 'data/berlin_tile_raster_template.tif'
# berlin_raster_image_counts = 'data/berlin_tile_raster.tif'

#test_city_tiles_path = 'data/test_city_tiles.csv'
#test_tiles_metadata_path = 'data/test_tiles_metadata.csv'
#test_image_selection_metadata_path = 'data/testimage_selection_metadata.csv'

test_city_tiles_path = 'data/{}/city_tiles.csv'
test_tiles_metadata_path = 'data/{}/all_images_metadata.csv'
test_image_selection_metadata_path = 'data/{}/image_selection_metadata.csv'
test_image_folder = 'data/{}/images'
test_small_raster_template = 'data/{}/small_raster_template.tif'
test_small_raster_counts = 'data/{}/small_raster_counts.tif'

boundary = 'data/{}/boundary.geojson'

train_tiles_metadata_path = 'data/train_tiles_metadata.csv'
train_tiles_selection_path = 'data/train_tiles_selection.csv'
train_image_selection_metadata_path = 'data/train_image_selection_metadata.csv'

token_path = 'mapillary_token.txt'

## global mapillary settings
mapillary_tile_url = 'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}'
tile_coverage = 'mly1_public'
tile_layer = "image" #"overview"
zoom = 14
image_size = "thumb_1024_url"

bbox_germany = [
    5.866240000000001,
    47.27011000000001,
    15.041880000000001,
    54.98310499999999,
]

# test cities
# bbox_luenburg = [10.324,53.191,10.542,53.295]
# bbox_cologne = [6.768,50.865,7.161,51.084]
# bbox_bamberg = [10.828,49.842,10.96,49.951]
# bbox_heilbronn = [9.04,49.094,9.303,49.21]
# bbox_dresden = [13.57,51.002,13.97,51.18]

# timestamp filter 1.6.2021
time_filter_unix = 1609891200000
max_img_per_sequence = 10
max_img_per_cell = 5

# training tiles
min_images = 500
min_tags = 50
