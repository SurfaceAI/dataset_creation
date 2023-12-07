# dataset_creation

Code to create our test and training data.

## Pre-study: find out mapillary image and tag counts per (mapbox) tile

*Data for Mapillary and OSM both taken from 20th November 2023.*


*> a file `mapillary_token.txt` needs to be created that holds the mapillary access token for the API and is placed in the root folder of this repo.*

[`mapillary_image_counts_per_tile.py`](/scripts/mapillary_image_counts_per_tile.py) is a script that queries the mapillary API and creates a csv where each row corresponds to one tile (x,y,z) with center lat / lon and image count information.

As mapillary has a rate limit, there are two tokens expected in the `mapillary_token.txt` which are rotated when the limit is reached.

[`create_raster_from_tiles.py`](/scripts/create_raster_from_tiles.py) is a script that creates a raster file (.tif) for the previously created csv file and each raster cell contains the image count.

[`osm_tag_counts_as_raster.sql`](/scripts/osm_tag_counts_as_raster.sql) is a SQL script that creates seperate rasters with counts of `asphalt`, `sett`, `paving_stones`, `unpaved`. It expects a database with an `.osm.pbf` file inserted. 

## Dataset creation

This is the [script](/scripts/train_test_data.py) for creation of train and test datasets.

### Step 1: create test data


- Selection of five cities as test data, which will be entirely excluded from the training data set. These cities are all in Germany but differ in their region (north, west, east, south-east, south-west) and in their size. We used cities with good mapillary image coverage.
    - Munich
    - Heidelberg
    - Cologne
    - Lüneburg
    - Dresden

For each city, we aim to obtain a diverse dataset. We thus restrict 
- the number of images per mapillary sequence to 10 images
- the number of images per 100mx100m grid cell to 5 images.

We further remove images from the Autobahn, as they take up a larger share of images, however, we are interested in classifying urban regions. (Autobahn has typically good/excellent asphalt).

We then sample 1000 images per city.

### Step 2: create training data

For the training data, our aim is to intersect mapillary images with OSM surface and smoothness tags and create a labeled dataset where each class (i.e, surface/smoothness combination) has 1000 images. The process of creating training data is still evolving. In the following section, you can read the filters applied in each version.

#### Dataset versions

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

**V3**

- sample from entire Germany.
- sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads
- **distance < 2 meters - then take *closest* road to img, if img intersects with multiple roads, not *random* road**
- 10% cut off at intersections (start and end of roads)
- **no filter by date**
- max **5** images per sequence
- about 100 images per class
- no panorama images
- filter, only relevant classes:
  - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
  - sett: good, intermediate, bad
  - unpaved: intermediate, bad, very_bad
- remove images in winter (dec, jan, feb)
- remove images at night (only between 8am and 6pm)


