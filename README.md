# Dataset creation

This repository implements the semi-automated image selection and pre-labeling strategies as described in this xxx publication. 
Images are sampled from Mapillary for manual annotation to create a dataset or street-level imagery on surface type and quality. 
This data can be used for training of classifiers of road surface type and quality.

**The final dataset is published [here](TODO).**

If you use this dataset, please cite as:
  TODO

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

[This](/src/scripts/00_create_dataset.py) is the entry point for creation of train and test datasets.
There, all 8 steps (+ 2 additional for catching annotation errors) are sequentially executed. Their respective scripts can be found in this [folder](/src/scripts/ds_creation_steps/).

These steps are the following:

### Create test data
- **[Step 0](/scripts/ds_creation_steps/s0_create_test_data.py): create test data**

- Selection of five cities as test data, which will be entirely excluded from the training data set. These cities are all in Germany but differ in their region (north, west, east, south-east, south-west) and in their size. We used cities with good Mapillary image coverage.
    - München (Munich)
    - Heilbronn
    - Köln (Cologne)
    - Lüneburg (Lunenburg)
    - Dresden

For each city, we aim to obtain a diverse dataset. We thus restrict 
- the number of images per Mapillary sequence to 10 images
- the number of images per 100mx100m grid cell to 5 images.

We further remove images from the Autobahn, as they take up a larger share of images, however, we are interested in classifying urban regions. (Autobahn has typically good/excellent asphalt).

We then sample 1000 images per city.

### Create training data
For the training data, our aim is to intersect Mapillary images with OSM surface and smoothness tags and create a labeled dataset.

- **[Step 1](/src/scripts/ds_creation_steps/s1_select_train_tiles.py): select train tiles**
  - exclude all tiles that are part of test data tiles
  - sample a subset from remaining tiles, to keep computational times in a reasonable limit (the sampling procedure evolved over different versions - see below)

- **[Step 2](/src/scripts/ds_creation_steps/s2_get_train_tiles_metadata.py): get train tiles metadata from mapillary**
  - query metadata (*id, sequence_id, captured_at, compass_angle, is_pano, creator_id, lon, lat*) for all Mapillary images within selected tiles
  - write metadata to csv file, but more importantly to the same database where the OSM data is stored

- **[Step 3](/src/scripts/ds_creation_steps/s3_intersect_mapillary_osm.py): intersect Mapillary with OSM**
  - intersects OSM streets with tags surface and smoothness with Mapillary image geolocations such that each image obtains a tag surface and smoothness (if a respective tag is provided in OSM)
  - exact intersection rules (e.g., max. distance between street and point) evolved over different versions - see below 

- **[Step 4](/src/scripts/ds_creation_steps/s4_select_train_images.py): select train images**
  - from all images, we now only consider images that obtained resepctive OSM tags
  - from remaining images, images are selected to certain criteria (again, they evolved over different versions - see below )
  - note, that this step requires output from a classification model which is not part of this repository

- **[Step 5](/scripts/ds_creation_steps/s5_download_train_images.py): download train images**
  - download selected images from Mapillary 

- **[Step 6](/scripts/ds_creation_steps/s6_prepare_manual_annotation.py): prepare manual annotation**
  - for manual annotation in Labelstudio, required files are prepared and sorted according to the number of annotators and batch sizes (data is annotated iteratively)

- **[Step 7](/scripts/ds_creation_steps/s7_prepare_image_folders.py): prepare image folders**
  - after data has been annotated, image folders are created according to the labels

To catch annotation errors, there are additionally:
- [Step 8](/scripts/ds_creation_steps/s8_relabel_misclassified_surfaces.py): for surface type
- [Step 9](/scripts/ds_creation_steps/s8_relabel_misclassified_qualities.py): for surface qualities

Model predictions and annotations are compared and those that differ from one another will be re-evaluated.


#### Dataset versions

The process of creating training data was evolving. In the following section, we documented the evolution up to the currently used version and considerations applied in each version.
Changes are marked in **bold**.

Generally, V0.0 to V0.3 were experiments to find a good sampling technique. Quality was determined by random viewing of samples to catch major issues.
We started labeling at **V0.4**.
**V0.5** is a *unlabled datapool*. Labels were added in iterations and new *labled dataset versions* were continuously created. Each new data version from V0.6 to V0.9 is the collection of all *labled images thus far*.  
V0.10 and V0.12 do not add further images, instead, they refine existing annotations with the goal of finding annotation errors. V0.11 additionally added a sample of 10% automatically discarded images in case of an introduced bias.

**V0.100, V0.101, V0.200 and 0.V5X** are new *datapools* for further experiments of semi-automated labeling for under-represented classes. Thus, they are not labeled systematically but only images that were algorithmically identified as belonging to under-represented classes were manually checked and if confirmed, added to the final dataset V1.0.

**V0.0**: 

First test with Berlin data.

- Sample from Berlin
- only roads that cars can drive on
- 5% of start and end of roads were cut off
- 10 meter buffer around streets


**V0.1**

- **sample from entire Germany**
- **sampling of 1000 random tiles with > 500 img per tile and  50 tagged roads**
- **buffer of 5 meters around each street which are intersected with Mapillary image coordinates**
- ***no* cut off at intersections (start and end of roads)**
- **only images after June 2021**
- **max 10 images per sequence**
- **about 100 images per class**
- **no panorama images**

**V0.2**

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

**V0.3**

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

**V0.4**

- sample from entire Germany.
- sampling of 1.000 random tiles with > 500 img per tile and  50 tagged roads
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


**V0.5**

- sample from entire Germany.
- sampling of train tiles:
  - **300 tiles per surface/smoothness combination where according to OSM at least a certain amount of streets hold this tag combination** (threshold set based on median of respective count distribution)
- Mapillary - OSM intersection: 
  - 10% cut off at intersections (start and end of roads)
  - distance < 2 meters - then take *closest* road to img, if img intersects with multiple roads, not *random* road
- Filter images from intersected image pool:
  - max **10** images per sequence
  - **max 5 images per mercantile tile**
  - no panorama images
  - filter, only relevant classes:
    - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
    - sett: good, intermediate, bad
    - unpaved: intermediate, bad, very_bad
  - about **2.000** images per class
    - **prefer pedestrian and cycleway**: take 500 images for surface/smoothness classification only from highway type "pedestrian" and "cycleway" (if not as many available, take max. images available). Fill rest of 1.500 images with remaining images. 

  
Dataset V5 is not labeled at once, but in different *chunks* which are continuously added to the stack of labeled images. However, each chunk is already used individually (or combined).
Thus, there are *subsets* of dataset **V0.5** named according to their chunk:

- c0 is a set of 180 images, which have been labeled by all three annotators to compute interrater reliability
- c1 is a set of 3x889=2667 images. (Initially, a set of 300 images per class was sampled from V5. Then, combined predictor (OSM label+model prediction based on V0.4)) was used and only images where both predictors agreed where included for labeling in c1, resulting in about half (2.667 from initially 5.400) of the images.
- c2 are all remaining images of asphalt of class *intermediate* and *bad* - according to OSM labels -  which are 2721 images. Again, using the current state of the classification model in combination with OSM tag, 1923 images remain where both predictors agree. These are then manually labeled.
- c3 are all remaining images of paving stones of class *bad* - according to OSM labels -  which are 256 images. From *excellent* and *intermediate* there are each 800 images.  
- c4 are all remaining images of paving stones of class *excellent* and *intermediate* (1.775 images in total).
- c5 are all remaining images of sett of class *bad* and *good* (2.433 images in total)
- c6 are all remaining images of concrete of class *bad* and *exellent* and 200 images of class intermediate  (692 images in total)
- c7 unpaved images of class *very_bad* (300) and *bad* (50) and *intermediate* (50) (400 images)

**V0.6**

A combination of labeled images from **V0.4**, *V0.5_c0** and **V0.5_c1**.


**V0.7**

A combination of labeled **asphalt** images from V0.4, V0.5_c0, V0.5_c1, **V0.5_c2**.

**V0.8**

A combination of labeled **paving_stones** images from V0.4, V0.5_c0, V0.5_c1, V0.5_c2, **V0.5_c3,  V0.5_c4**.

**V0.9**

A combination  **all** labeled images from V0.4, V0.5_c0, V0.5_c1, V0.5_c2, V0.5_c3, V0.5_c4, **V0.5_c5, V0.5_c6, V0.5_c7**.

**V0.10** 
All images in V0.9 are used as training data and then predicted. All images where prediction and true label are not matching are revised, to catch annotation errors. (44 annotations from 350 misclassifications were adjusted.)

**V0.11**
All images from V0.10 and additionally a **subset of 10% of all images that were filtered out (by the model) in previous steps** are labeled. We include this step in case there is a systematic bias of images that are excluded by the model.

**V0.12**

All images from V0.11. All **paving stones quality** images where prediction and true label deviate more than 1 are **revised** to catch annotation errors (36 quality classifications were adjusted, 4 surface classifications.)

**V0.100**

A new datapool similar to V0.5 is created as a base to sample more images of underrepresented images.

Pre-selection of tiles:
  - Tile selection based on OSM Tag pre-selection: 
    - **600** tiles per **relevant** (asphalt - intermediate, bad; paving stones - excellent, intermediate, bad; sett - good; all concrete; all unpaved) surface/smoothness combination where according to OSM at least a certain amount of streets hold this tag combination
    (threshold set based on median of respective count distribution)

  - Filter images from intersected image pool:
  - no panorama images
  - filter, only relevant classes:
    - asphalt / concrete / paving_stones: excellent, good, intermediate, bad
    - sett: good, intermediate, bad
    - unpaved: intermediate, bad, very_bad
  - **Filter per surface/smoothness class**:
    - max **5** images per sequence
    - max 5 images per mercantile tile
    - about **3.000** images per class
      - prefer pedestrian and cycleway: take 500 images for surface/smoothness classification only from highway type "pedestrian" and "cycleway" (if not as many available, take max. images available). Fill rest with remaining images. 

  - c1: asphalt bad & intermediate (up to 2.500 images per class)
  - c2: paving stones excellent, intermediate, bad (up to 2.500 images per class)


##### For further experiments new (unlabeled) datapools were required. For these, we created the following:

**V0.5X**

V0.5X creates a new metadata selection out of the V0.5 metadata pool. It thereby uses less strict restrictions:
- sequence and tile ID is not limited globally to 5 anymore, but by surface/smoothness class
- any image part of a sequence and tile that has not exhausted this restriction, will be considered a potential sample again
- from potential images, samples are drawn such that each sequence and tile is "filled up" up to the limit of 5

  - c1: asphalt bad (up to 2.500 images per class)
  - c2: paving stones excellent, intermediate, bad (up to 2.500 images per class)

**V0.101**

Combination of V0.100 c1, c2 and V0.5X c1, c2.

**V0.200**

New datapool *without OSM based pre-selection*.

- tile selection: 5.000 tiles with at least 500 images, randomly drawn (can be same as V0.5 / V0.100)
- random 20.000 images sampled
  - max. 5 per tile
  - max. 10 per sequence

  **V1.0**