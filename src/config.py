import os
import constants as const


# location of data folder
data_folder = "data"

## mapillary settings
token_path = os.path.join("mapillary_token.txt")
mapillary_tile_url = "https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}"
mapillary_graph_url = "https://graph.mapillary.com/{}"
tile_coverage = "mly1_public"
tile_layer = "image"  # "overview"
zoom = 14
image_size = "thumb_1024_url"

# train data paramenters
ds_version = "v103"
max_img_per_sequence_train = 5
max_img_per_tile = 5
tile_sample_size = 500
min_images = 500
# min_tags = 50
ds_tile_count = 5000

imgs_per_class = 2500

# test data paramenters
# timestamp filter 1.6.2021
time_filter_unix = 1609891200000
max_img_per_sequence_test = 2
max_img_per_cell = 2
sample_size_test_city = 200

# center bounding box
center_bboxes = {
    const.COLOGNE: {
        "xmin": 6.925906,
        "xmax": 6.998256,
        "ymin": 50.911576,
        "ymax": 50.956255,
    },
    const.DRESDEN: {
        "xmin": 13.709555,
        "xmax": 13.781723,
        "ymin": 51.02781,
        "ymax": 51.067380,
    },
    const.MUNICH: {
        "xmin": 11.52477,
        "xmax": 11.62034,
        "ymin": 48.09620,
        "ymax": 48.16591,
    },
    const.HEILBRONN: {
        "xmin": 9.044609,
        "xmax": 9.301967,
        "ymin": 49.092888,
        "ymax": 49.209728,
    },
        const.LUNENBURG: {
        "xmin": 10.330825,
        "xmax": 10.514356,
        "ymin": 53.191676,
        "ymax": 53.286644,
    },
}

##labelstudio
n_annotators = 3
# n img per class for for interrater reliability
n_irr = 10

chunk_ids = [2]
# n img per cluss for each chunk when annotating
# n_per_chunk = 100

cloud_image_folder = (
    "/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/"
)

model_prediction_path = os.path.join(cloud_image_folder, "training", "{}", "metadata")
model_prediction_file = {
    "v5c1": "model_predictions_V5_c1_predicted.csv",
    "v5c2": "surface_prediction-V5_c2-20240215_143635.csv",
    "v5c3": "surface_prediction-V5_c3-20240222_122429.csv",
    "v5c4": "surface_prediction-V5_c4-20240226_150406.csv",
    "v5c5": "surface_prediction-V5_c5-20240226_155720.csv",
    "v5c6": "surface_prediction-V5_c6-20240305_171454.csv",
    "v5c7": "surface_prediction-V5_c7-20240306_100314.csv",
    "v101": "effnet_surface_quality_prediction-V101_unsorted_images-20240513_005444.csv",
    "v102": "effnet_surface_quality_prediction-V102_unsorted_images-20240530_083702.csv",
    "v103": "effnet_surface_quality_prediction-V103_unsorted_images-20240601_111055.csv",
    "v200": "effnet_surface_quality_prediction-V200-20240515_103743.csv"
}

manual_added_images = os.path.join(
    cloud_image_folder,
    "training",
    "{}_c{}",
    "metadata",
    "incorrect_filtered_images.txt",
)
labelstudio_absolute_path = "https://freemove.f4.htw-berlin.de/data/local-files/?d={}"
labelstudio_predictions_path = os.path.join(
    cloud_image_folder, "training", "{}", "sample_predictions.json"
)
# img ids that have previously already been labeled and should be excluded in further labeling to avoid redundant work
labeled_imgids_path = os.path.join(data_folder, "labeled_imgids.txt")
chunks_folder = os.path.join(data_folder, "{}", "chunks")
interrater_reliability_img_ids_path = os.path.join(
    chunks_folder, "interrater_reliability_img_ids.{}"
)
chunk_img_ids_path = os.path.join(chunks_folder, "c{}_img_ids.{}")
chunk_filtered_img_ids_path = os.path.join(chunks_folder, "c{}_filtered_out_img_ids.{}")
annotator_ids_path = os.path.join(chunks_folder, "c{}_annotator{}_img_ids.{}")

# test data
test_labelstudio_input_path = os.path.join(
    data_folder, "test_data", "{}", "labelstudio_input.json"
)


# possible surface / smoothness combinations
surfaces = [
    const.ASPHALT,
    const.CONCRETE,
    const.PAVING_STONES,
    const.SETT,
    const.UNPAVED,
]

surf_smooth_comb = {
    const.ASPHALT: [const.EXCELLENT, const.GOOD, const.INTERMEDIATE, const.BAD],
    const.CONCRETE: [const.EXCELLENT, const.GOOD, const.INTERMEDIATE, const.BAD],
    const.PAVING_STONES: [const.EXCELLENT, const.GOOD, const.INTERMEDIATE, const.BAD],
    const.SETT: [const.GOOD, const.INTERMEDIATE, const.BAD],
    const.UNPAVED: [const.INTERMEDIATE, const.BAD, const.VERY_BAD],
}


# PATHS

# file paths for tif files (mapillary image counts and OSM tag counts as rasters)
tag_counts_path = os.path.join(data_folder, "tag_counts")
surf_smooth_tag_counts_path = os.path.join(tag_counts_path, "{}_{}_counts_germany.tif")
germany_tiles_path = os.path.join(tag_counts_path, "germany_image_counts.csv")
germany_raster_template_path = os.path.join(
    tag_counts_path, "germany_tile_raster_template.tif"
)

autobahn_path = os.path.join(data_folder, "autobahn.shp")
filtered_autobahn_path = os.path.join(
    data_folder, "test_data", "{}", "autobahn_filtered.geojson"
)
# test city paths (bracket will be filled with city name)
test_data_folder = os.path.join(data_folder, "test_data")
test_city_tiles_path = os.path.join(test_data_folder, "{}", "city_tiles.csv")
test_tiles_metadata_path = os.path.join(
    test_data_folder, "{}", "all_images_metadata.csv"
)
test_image_selection_metadata_path = os.path.join(
    test_data_folder, "{}", "image_selection_metadata.csv"
)
test_image_folder = os.path.join(test_data_folder, "{}", "images")
test_small_raster_template = os.path.join(
    test_data_folder, "{}", "small_raster_template.tif"
)
test_small_raster_counts = os.path.join(
    test_data_folder, "{}", "small_raster_counts.tif"
)
test_image_metadata_with_tags_path = os.path.join(
    test_data_folder, "{}", "img_metadata_with_tags.csv"
)
boundary = os.path.join(test_data_folder, "{}", "boundary.geojson")

# train data paths (bracket will be filled with training data version)
train_tiles_metadata_path = os.path.join(data_folder, "{}", "train_tiles_metadata.csv")
train_tiles_selection_path = os.path.join(
    data_folder, "{}", "train_tiles_selection.csv"
)
train_image_selection_metadata_path = os.path.join(
    data_folder, "{}", "train_image_selection_metadata.csv"
)
train_image_folder = os.path.join(data_folder, "{}", "train_images")
chunk_image_folder = os.path.join(train_image_folder, "c{}")
train_image_metadata_with_tags_path = os.path.join(
    data_folder, "{}", "img_metadata_with_tags.csv"
)

# sql scripts
sql_scripts_path = os.path.join("src", "scripts", "sql")
sql_script_intersect_osm_mapillary_path = os.path.join(
    sql_scripts_path, "intersect_osm_mapillary.sql"
)
sql_script_save_db_to_csv_path = os.path.join(sql_scripts_path, "save_db_to_csv.sql")
sql_script_mapillary_meta_to_database_path = os.path.join(
    sql_scripts_path, "mapillary_meta_to_database.sql"
)
sql_script_osm_tags_to_raster_counts_path = os.path.join(
    sql_scripts_path, "osm_tag_counts_as_raster.sql"
)
