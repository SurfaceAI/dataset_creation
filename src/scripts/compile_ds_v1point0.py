import pandas as pd
from tqdm import tqdm
import os

import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import src.utils as utils
import src.config as config


v12 = pd.read_csv(os.path.join(config.cloud_image_folder, "training", "V12", "metadata", "annotations_combined.csv"), dtype={"image_id": str})
label_corrections = pd.read_csv(os.path.join(config.cloud_image_folder, "training", "img_label_corrections.csv"), dtype={"image_id": str})

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

v101 = pd.read_csv(os.path.join(config.cloud_image_folder, "automated_labeling_experiments", "annotations_combined", "V101.csv"))
v200 = pd.read_csv(os.path.join(config.cloud_image_folder, "automated_labeling_experiments", "annotations_combined", "V200.csv"))
vexp = pd.concat([v101, v200])
vexp["image_id"] = vexp.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: str.split(x, ".jpg")[0]
    )
vexp.loc[vexp.nostreet.notna(), "surface"] = "nostreet"
vexp.loc[vexp.nostreet.notna(), "smoothness"] = "nostreet"
vexp.loc[vexp.correct.isin(["no", "revise"]), "surface"] = "false"
vexp.loc[vexp.correct.isin(["no", "revise"]), "smoothness"] = "false"
vexp = vexp[~vexp.surface.isin(["nostreet", "false"] )]

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


test_cities = ["dresden", "munich", "cologne", "luenenburg", "heilbronn"] 

tc_data = pd.DataFrame()
for test_city in test_cities:
    test_city_path = os.path.join(config.cloud_image_folder, "test", "{}", "metadata", "{}_annotations.csv")
    tc = pd.read_csv(test_city_path.format(test_city, test_city))
    tc.rename({"surface": "surface_car", "smoothness": "smoothness_car"}, axis=1, inplace=True)
    tc = tc[tc.nostreet.isna()]
    tc = tc[tc.focus != "no focus"]
    tc[["surface", "smoothness", "roadtype"]] = tc.apply(get_surface, axis=1, result_type="expand")
    tc = tc[~tc.surface.isin(["not recognizable", "surface not in category", "non-existent"])]
    tc = tc[~tc.smoothness.isin(["not recognizable"])]
    tc_data = pd.concat([tc_data, tc])

tc_data["image_id"] = tc_data.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: str.split(x, ".jpg")[0]
    )
tc_data["train"] = False
# combine both datasets
# image_id, surface_type, surface_quality, train
v1point0 = pd.concat([v1point0, tc_data[["image_id", "surface", "smoothness", "roadtype", "train"]]])

v1point0 = v1point0[v1point0.surface.notna()]
v1point0 = v1point0[v1point0.smoothness.notna()]
v1point0.rename({"image_id": "mapillary_image_id", "surface": "surface_type", "smoothness": "surface_quality"}, axis=1, inplace=True)

# make sure there are no duplicates
v1point0.drop_duplicates("mapillary_image_id", inplace=True)
# make sure all ids are strings
v1point0.mapillary_image_id = v1point0.mapillary_image_id.astype(str)



# download images in all resolutions and get metadata (user_id, user_name, captured_at, latitude, longitude)

img_sizes = ["256", "1024", "2048", "original"]
dest_folder = os.path.join(config.cloud_image_folder, "V1_0")

errors = []
for img_size in img_sizes:
    img_size_folder = f"s_{img_size}"
    img_size_dest_folder = os.path.join(dest_folder, img_size_folder)
    os.makedirs(img_size_dest_folder, exist_ok=True)
    existing_files = os.listdir(img_size_dest_folder)
    for img_id in tqdm(v1point0.mapillary_image_id.tolist()):
        if str(img_id) + ".jpg" in existing_files:
            continue
        no_error = utils.download_image(
            int(img_id), img_size_dest_folder, f"thumb_{img_size}_url"
        )
        if no_error == False:
            errors.append([img_id, img_size])

pd.DataFrame(errors, columns=["mapillary_image_id", "img_size"]).to_csv(os.path.join(dest_folder, "V1_0_errors.csv"))

errors = []
metadata = []
#### get additional metadata

old_v1point0 = pd.read_csv(os.path.join(dest_folder, "streetSurfaceVis_v1_0.csv"), dtype={"mapillary_image_id": str})

for img_id in tqdm(v1point0.mapillary_image_id.tolist()):
    if old_v1point0[old_v1point0.mapillary_image_id == img_id].shape[0] > 0:
        old_values = old_v1point0[old_v1point0.mapillary_image_id == img_id][["captured_at","user_id","user_name","longitude","latitude"]].values.tolist()[0]
        metadata.append([img_id] + old_values)
    else:
        metadata_img = utils.get_metadata(img_id)
        if metadata_img == False:
            errors.append(img_id)
        else:
            metadata.append([img_id] + metadata_img)

v1point0_metadata = v1point0.join(pd.DataFrame(metadata, columns = ["mapillary_image_id","captured_at","user_id","user_name","longitude","latitude"]).set_index("mapillary_image_id"), 
              on="mapillary_image_id")

pd.DataFrame(errors, columns=["mapillary_image_id"]).to_csv(os.path.join(dest_folder, "V1_0_errors_metadata.csv"))


##### remove all errors from dataset (csv) ####
errors = pd.read_csv(os.path.join(dest_folder, "V1_0_errors.csv"), dtype={"mapillary_image_id": str})
v1point0_metadata = v1point0_metadata[~v1point0_metadata.mapillary_image_id.isin(errors.mapillary_image_id)]

errors = pd.read_csv(os.path.join(dest_folder, "V1_0_errors_metadata.csv"),  dtype={"mapillary_image_id": str})
v1point0_metadata = v1point0_metadata[~v1point0_metadata.mapillary_image_id.isin(errors.mapillary_image_id)]

########

v1point0_metadata["user_id"] = v1point0_metadata["user_id"].astype(int)
v1point0_metadata["captured_at"] = v1point0_metadata["captured_at"].astype(int)
(v1point0_metadata[["mapillary_image_id", "user_id", "user_name", "captured_at", "longitude","latitude", "train", "surface_type", "surface_quality"]]
        .to_csv(os.path.join(dest_folder, "streetSurfaceVis_v1_0.csv"), index=False)
)
(
v1point0_metadata[["mapillary_image_id", "user_id", "user_name", "captured_at", "longitude","latitude", "train", "surface_type", "surface_quality", "roadtype"]]
        .to_csv(os.path.join(dest_folder, "v1_0_incl_roadtype.csv"), index=False)
)


# remove any images from folders that are not within the dataset anymore

v1point0 = pd.read_csv(os.path.join(dest_folder, "streetSurfaceVis_v1_0.csv"), dtype={"mapillary_image_id": str})
image_ids = set(v1point0['mapillary_image_id'])
img_folder = os.path.join(dest_folder, "{}")
sizes = ["256", "1024", "2048", "original"]

for size in sizes:
    img_folder_size = img_folder.format(f"s_{size}")

    # Get a list of all files in the images directory
    image_files = os.listdir(img_folder_size)

    # Iterate over the image files
    counter = 0
    for image_file in image_files:
        # If the file is not in the set of image ids, remove it
        img_id = image_file.split(".")[0]
        if img_id not in image_ids:
            counter += 1
            os.remove(os.path.join(img_folder_size, image_file))
    print(counter)