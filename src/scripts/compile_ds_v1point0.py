import pandas as pd
from tqdm import tqdm
import os

import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import src.utils as utils

v12 = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V12/metadata/annotations_combined.csv", dtype={"image_id": str})
label_corrections = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/img_label_corrections.csv", dtype={"image_id": str})

# overwrite labels (TODO vectorize)
for i, row in label_corrections.iterrows():
    image_id = row["image_id"]
    if image_id in list(v12.image_id):
        surface = row["surface"]
        smoothness = row["smoothness"]
        nostreet = row["nostreet"]
        v12.loc[v12.image_id == image_id, "surface"] = surface
        v12.loc[v12.image_id == image_id, "smoothness"] = smoothness
        v12.loc[v12.image_id == image_id, "nostreet"] = nostreet

v12 = v12[v12.nostreet.isna()]
v12["train"] = True
v1point0 = v12[["image_id", "surface", "smoothness", "roadtype", "train"]]

##################### add images from experiments ####################

v101 = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/automated_labeling_experiments/annotations_combined/V101.csv")
v200 = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/automated_labeling_experiments/annotations_combined/V200.csv")
vexp = pd.concat([v101, v200])
vexp["image_id"] = vexp.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: int(str.split(x, ".jpg")[0])
    )
vexp.loc[vexp.nostreet.notna(), "surface"] = "nostreet"
vexp.loc[vexp.nostreet.notna(), "smoothness"] = "nostreet"
vexp = vexp[vexp.surface != "nostreet"]
vexp["train"] = True
v1point0 = pd.concat([v1point0, vexp[["image_id", "surface", "smoothness", "roadtype", "train"]]])


#v1point0.groupby(["surface", "smoothness"]).size()


############### add test cities ###############
def get_surface(row):
    if row.focus == "car/path in focus":
        return (row.surface_car, row.smoothness_car, "road / path")
    elif row.focus == "pedestrian in focus":
        return (row.surface_pedestrian, row.smoothness_pedestrian, "pedestrian")
    elif row.focus == "cycleway in focus":
        return (row.surface_cycleway, row.smoothness_cycleway, "cycleway")


test_cities = ["dresden", "munich", "cologne", "luenenburg", "heilbronn"] #luenenburg, heilbronn

tc_data = pd.DataFrame()
for test_city in test_cities:
    test_city_path = "/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/test/{}/metadata/{}_annotations.csv"
    tc = pd.read_csv(test_city_path.format(test_city, test_city))
    tc.rename({"surface": "surface_car", "smoothness": "smoothness_car"}, axis=1, inplace=True)
    tc = tc[tc.nostreet.isna()]
    tc = tc[tc.focus != "no focus"]
    tc[["surface", "smoothness", "roadtype"]] = tc.apply(get_surface, axis=1, result_type="expand")
    tc = tc[~tc.surface.isin(["not recognizable", "surface not in category"])]
    tc = tc[~tc.smoothness.isin(["not recognizable"])]
    tc_data = pd.concat([tc_data, tc])

tc_data["image_id"] = tc_data.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: int(str.split(x, ".jpg")[0])
    )
tc_data["train"] = False
# combine both datasets
# image_id, surface_type, surface_quality, train
v1point0 = pd.concat([v1point0, tc_data[["image_id", "surface", "smoothness", "roadtype", "train"]]])
v1point0.rename({"image_id": "mapillary_image_id", "surface": "surface_type", "smoothness": "surface_quality"}, axis=1, inplace=True)

# make sure there are no duplicates
v1point0.drop_duplicates("mapillary_image_id", inplace=True)
v1point0.drop("roadtype", axis=1).to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/V1_0/v1_0.csv")
v1point0.to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/V1_0/v1_0_incl_roadtype.csv")


# download images in all resolutions and get metadata (user_id, user_name, captured_at, latitude, longitude)

img_sizes = ["thumb_256_url", "thumb_1024_url", "thumb_2048_url", "thumb_original_url"]
dest_folder = "/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/V1_0"

errors = []
for img_size in img_sizes:
    img_size_dest_folder = os.path.join(dest_folder, img_size)
    os.makedirs(img_size_dest_folder, exist_ok=True)
    existing_files = os.listdir(img_size_dest_folder)
    for img_id in tqdm(v1point0.mapillary_image_id.tolist()):
        if str(img_id) + ".jpg" in existing_files:
            continue
        no_error = utils.download_image(
            int(img_id), img_size_dest_folder, img_size
        )
        if no_error == False:
            errors.append([img_id, img_size])

pd.DataFrame(errors).to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/V1_0_errors.csv")