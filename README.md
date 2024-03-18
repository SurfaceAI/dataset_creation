# Dataset creation

This repository contains the code to create our test and training data for the training and evaluation of classifiers of road surface and smoothness (quality).

## Prerequisites

### Mappillary Token

- a file `mapillary_token.txt` needs to be created that holds the Mapillary access token for the API and is placed in the root folder of this repo.
As Mapillary has a rate limit, there are two tokens expected in the `mapillary_token.txt` which are rotated when the limit is reached.


### OSM database

- a PostGIS database that holds all streets of OSM for Germany is expected. Therefore, `osmosis` is used (requires prior installation of postgresql, postgis, osmosis):
```bash
    createdb osmGermany
    psql  -d osmGermany -c  'CREATE EXTENSION postgis;'
    psql  -d osmGermany -c  'CREATE EXTENSION hstore;'

    # Download the osmosis setup script: https://github.com/openstreetmap/osmosis/releases/tag/0.48.3
    psql -d osmGermany -f osmosis-0.48.3/script/pgsnapshot_schema_0.6.sql

    osmosis --read-pbf germany-latest.osm.pbf --tf accept-ways 'highway=*' --used-node --tf reject-relations --log-progress --write-pgsql database=osmGermany
```

a `database_credential.py` file is expected in the root folder in the format of:

    database = "osmGermany"
    user = "USER_NAME"
    host = "HOST"

*For our run, metadata for Mapillary and OSM both taken from 20th November 2023.*


## Dataset creation

[This](/scripts/train_test_data.py) is the entry point for creation of train and test datasets.
There, all 7 steps are sequentially executed. Their respective scripts can be found in this [folder](/scripts/ds_creation_steps/).

These steps are the following:

### Create test data
- **[Step 0](/scripts/ds_creation_steps/s0_create_test_data.py): create test data**

- Selection of five cities as test data, which will be entirely excluded from the training data set. These cities are all in Germany but differ in their region (north, west, east, south-east, south-west) and in their size. We used cities with good Mapillary image coverage.
    - München (Munich)
    - Heidelberg
    - Köln (Cologne)
    - Lüneburg (Lunenburg)
    - Dresden

For each city, we aim to obtain a diverse dataset. We thus restrict 
- the number of images per Mapillary sequence to 10 images
- the number of images per 100mx100m grid cell to 5 images.

We further remove images from the Autobahn, as they take up a larger share of images, however, we are interested in classifying urban regions. (Autobahn has typically good/excellent asphalt).

We then sample 1000 images per city.

### Create training data
For the training data, our aim is to intersect Mapillary images with OSM surface and smoothness tags and create a labeled dataset where each class (i.e, surface/smoothness combination) has 1000 images.

- **[Step 1](/scripts/ds_creation_steps/s2_get_train_tiles_metadata.py): select train tiles**
  - exclude all tiles that are part of test data tiles
  - sample a subset from remaining tiles, to keep computational times in a reasonable limit (the sampling procedure evolved over different versions - see below)

- **[Step 2](/scripts/ds_creation_steps/s2_get_train_tiles_metadata.py): get train tiles metadata from mapillary**
  - query metadata (*id, sequence_id, captured_at, compass_angle, is_pano, creator_id, lon, lat*) for all Mapillary images within selected tiles
  - write metadata to csv file, but more importantly to the same database where the OSM data is stored

- **[Step 3](/scripts/ds_creation_steps/s3_intersect_mapillary_osm.py): intersect Mapillary with OSM**
  - intersects OSM streets with tags surface and smoothness with Mapillary image geolocations such that each image obtains a tag surface and smoothness (if a respective tag is provided in OSM)
  - exact intersection rules (e.g., max. distance between street and point) evolved over different versions - see below 

- **[Step 4](/scripts/ds_creation_steps/s4_select_train_images.py): select train images**
  - from all images, we now only consider images that obtained resepctive OSM tags
  - from remaining images, images are selected to certain criteria (again, they evolved over different versions - see below )

- **[Step 5](/scripts/ds_creation_steps/s5_download_train_images.py): download train images**
  - download selected images from Mapillary 

- **[Step 6](/scripts/ds_creation_steps/s6_prepare_manual_annotation.py): prepare manual annotation**
  - for manual annotation in Labelstudio, required files are prepared and sorted according to the number of annotators and batch sizes (data is annotated iteratively)

- **[Step 7](/scripts/ds_creation_steps/s7_prepare_image_folders.py): prepare image folders**
  - after data has been annotated, image folders are created according to the labels


### Dataset versions

The process of creating training data was evolving. In the following section, we documented the evolution up to the currently used version and considerations applied in each version.
Changes are marked in **bold**.

**V0**: 

First test with Berlin data. See [script](https://github.com/SurfaceAI/internal_code_snippets/blob/main/intersect_mapillary_points_and_roads.sql) in internal code snippets.

- Sample from Berlin
- only roads that cars can drive on
- 5% of start and end of roads were cut off
- 10 meter buffer around streets


**V1**

- **sample from entire Germany**
- **sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads**
- **buffer of 5 meters around each street which are intersected with Mapillary image coordinates**
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

  
Dataset V5 is not labeled at once, but in different *chunks* which are continuously added to the stack of labeled images. However, each chunk is already used individually (or combined).
Thus, there are *subsets* of dataset **V5** named according to their chunk:

- c0 is a set of 180 images, which have been labeled by all three annotators to compute interrater reliability
- c1 is a set of 3x889=2667 images. (Initially, a set of 300 images per class was sampled from V5. Then, combined predictor (OSM label+model prediction based on V4)) was used and only images where both predictors agreed where included for labeling in c1, resulting in about half (2667 from initially 5400) of the images.
- c2 are all remaining images of asphalt of class *intermediate* and *bad* - according to OSM labels -  which are 2721 images. Again, using the current state of the classification model in combination with OSM tag, 1923 images remain where both predictors agree. These are then manually labeled.

**V6**

A combination of labeled images from **V4**, *V5_c0** and **V5_c1**.


**V7**

A combination of labeled **asphalt** images from V4, V5_c0, V5_c1, **V5_c2**.
