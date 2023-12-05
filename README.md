# dataset_creation

Code to create our test and training data.

## Pre-study: find out image and tag counts and their distribution

*Data for Mapillary and OSM both taken from 20th November 2023.*


-> a file `mapillary_token.txt` needs to be created that holds the mapillary access token for the API and is placed in the root folder of this repo.

[`mapillary_image_counts_per_tile.py`]() is a script that queries the mapillary API and creates a csv where each row corresponds to one tile (x,y,z) with center lat / lon and image count information.

As mapillary has a rate limit, there are two tokens expected in the `mapillary_token.txt` which are rotated when the limit is reached.

[`create_raster_from_tiles.py`]() is a script that creates a raster file (.tif) for the previously created csv file and each raster cell contains the image count.

[`count_tags_in_osm_database.sql`] is a SQL script that creates seperate rasters with counts of `asphalt`, `sett`, `paving_stones`, `unpaved`. It expects a database with an `.osm.pbf` file inserted. 

## Dataset versions

**V0**: 

First test with Berlin data. See [script](https://github.com/SurfaceAI/internal_code_snippets/blob/main/intersect_mapillary_points_and_roads.sql) in internal code snippets.

- Sample from Berlin
- only roads that cars can drive on
- 5% of start and end of roads were cut off
- 10 meter buffer around streets


**V1**

- sample from entire Germany.
- sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads
- buffer of 5 meters
- *no* cut off at intersections (start and end of roads)
- only images after June 2021
- max 10 images per sequence
- about 100 images per class
- no panorama images

**V2**

- sample from entire Germany.
- sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads
- buffer of **1** meters
- **10%** cut off at intersections (start and end of roads)
- only images after June 2021
- max 10 images per sequence
- about 100 images per class
- no panorama images
- **filter, only relevant classes:**
  - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
  - sett: good, intermediate, bad
  - unpaved: intermediate, bad, very_bad
- **remove images in winter (dec, jan, feb)**
- **remove images at night (only between 8am and 6pm)**

