# dataset_creation

Code to create our test and training data.

## Pre-study: find out image and tag counts and their distribution

*Data for Mapillary and OSM both taken from 20th November 2023.*


-> a file `mapillary_token.txt` needs to be created that holds the mapillary access token for the API and is placed in the root folder of this repo.

[`mapillary_image_counts_per_tile.py`]() is a script that queries the mapillary API and creates a csv where each row corresponds to one tile (x,y,z) with center lat / lon and image count information.

As mapillary has a rate limit, there are two tokens expected in the `mapillary_token.txt` which are rotated when the limit is reached.

[`create_raster_from_tiles.py`]() is a script that creates a raster file (.tif) for the previously created csv file and each raster cell contains the image count.

[`count_tags_in_osm_database.sql`] is a SQL script that creates seperate rasters with counts of `asphalt`, `sett`, `paving_stones`, `unpaved`. It expects a database with an `.osm.pbf` file inserted. 

