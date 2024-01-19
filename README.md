# Dataset creation

Code to create our test and training data and other relevant statistics.

*> a file `mapillary_token.txt` needs to be created that holds the mapillary access token for the API and is placed in the root folder of this repo.*

*For our run, metadata for Mapillary and OSM both taken from 20th November 2023.*

## Scripts

You can find all scripts in the folder `scripts`. 

### Pre-study: find out mapillary image and tag counts per (mercantile) tile

[`mapillary_image_counts_per_tile.py`](/scripts/mapillary_image_counts_per_tile.py) is a script that queries the mapillary API and creates a csv where each row corresponds to one tile (x,y,z) with center lat / lon and image count information.

As mapillary has a rate limit, there are two tokens expected in the `mapillary_token.txt` which are rotated when the limit is reached.

[`create_raster_from_tiles.py`](/scripts/create_raster_from_tiles.py) is a script that creates a raster file (.tif) for the previously created csv file and each raster cell contains the image count.

[`osm_tag_counts_as_raster.py`](/scripts/osm_tag_counts_as_raster.py) is a python wrapper script for mostly SQL code that creates seperate rasters with counts of `asphalt`, `sett`, `paving_stones`, `unpaved`. It expects a database with an `.osm.pbf` file inserted. The database credentials are expected to be in a file `database_credentials.py` (`database`, `user`, `host`).

## Dataset creation

This is the (most relevant) [script](/scripts/train_test_data.py) for creation of train and test datasets.

The procedure is as follows:

### Step 1: create test data


- Selection of five cities as test data, which will be entirely excluded from the training data set. These cities are all in Germany but differ in their region (north, west, east, south-east, south-west) and in their size. We used cities with good mapillary image coverage.
    - München
    - Heidelberg
    - Köln
    - Lüneburg
    - Dresden

For each city, we aim to obtain a diverse dataset. We thus restrict 
- the number of images per mapillary sequence to 10 images
- the number of images per 100mx100m grid cell to 5 images.

We further remove images from the Autobahn, as they take up a larger share of images, however, we are interested in classifying urban regions. (Autobahn has typically good/excellent asphalt).

We then sample 1000 images per city.

### Step 2: create training data

For the training data, our aim is to intersect mapillary images with OSM surface and smoothness tags and create a labeled dataset where each class (i.e, surface/smoothness combination) has 1000 images. The process of creating training data is still evolving. In the following section, you can read the filters and considerations applied in each version.

Changes are marked in **bold**.

#### Dataset versions

**V0**: 

First test with Berlin data. See [script](https://github.com/SurfaceAI/internal_code_snippets/blob/main/intersect_mapillary_points_and_roads.sql) in internal code snippets.

- Sample from Berlin
- only roads that cars can drive on
- 5% of start and end of roads were cut off
- 10 meter buffer around streets


**V1**

- **sample from entire Germany**
- **sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads**
- **buffer of 5 meters around each street which are intersected with mapillary image coordinates**
- ***no* cut off at intersections (start and end of roads)**
- **only images after June 2021**
- **max 10 images per sequence**
- **about 100 images per class**
- **no panorama images**

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


**V4**

- sample from entire Germany.
- sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads
- distance < 2 meters - then take *closest* road to img, if img intersects with multiple roads, not *random* road
- 10% cut off at intersections (start and end of roads)
- no filter by date
- max 5 images per sequence
- about **100** images per class
- no panorama images
- filter, only relevant classes:
  - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
  - sett: good, intermediate, bad
  - unpaved: intermediate, bad, very_bad
- **do not** remove images in winter (dec, jan, feb) **> such that they can be included in the "no classification possible class**
- **do not** remove images at night (only between 8am and 6pm) **> such that they can be included in the "no classification possible class**

**V5**

- sample from entire Germany.
- sampling of train tiles:
  - more than 500 img per tile
  - **300 tiles per surface/smoothness combination where according to OSM at least a certain amount of streets hold this tag combination** (threshold set based on median of respective count distribution)
- Mapillary - OSM intersection: 
  - 10% cut off at intersections (start and end of roads)
  - distance < 2 meters - then take *closest* road to img, if img intersects with multiple roads, not *random* road
- Filter images from intersected image pool:
  - max 5 images per sequence
  - **max 20 images per mercantile tile**
  - no panorama images
  - filter, only relevant classes:
    - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
    - sett: good, intermediate, bad
    - unpaved: intermediate, bad, very_bad
  - about **2000** images per class
    - **prefer pedestrian and cycleway**: take 500 images for surface/smoothness classification only from highway type "pedestrian" and "cycleway" (if not as many available, take max. images available). Fill rest of 1.500 images with remaining images. 
