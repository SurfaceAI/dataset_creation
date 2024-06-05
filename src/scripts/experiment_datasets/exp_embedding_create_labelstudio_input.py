import os
import sys
from pathlib import Path

from tqdm import tqdm
import shutil

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import pandas as pd

import config
import utils
import scripts.ds_creation_steps.s6_prepare_manual_annotation as s6

# GPT results

surface = "paving_stones"
smoothness = "intermediate"
batch_id = 1
exp_id = 1
ds_version = 101

# TODO: filter exp. 1 images for paving stones
if exp_id == 1:
    img_folder = f"V{ds_version}/{surface}/{smoothness}"
    crop_folder = f"{smoothness}/gpt_selection_crop"
elif exp_id == 2:
    crop_folder = f"{smoothness}_crop"
    if batch_id == 2:
        additional_name = "_excl_no_focus"
    else:
        additional_name = ""
df = pd.read_csv(os.path.join(Path(config.cloud_image_folder).parent, "mapillary_images", "automated_labeling_experiments",
                            "embedding_experiments", "results", f"V{ds_version}_effnet_{surface}_{smoothness}_gpt_combined.csv"))

df = df[(df.in_gpt == False) & (df.prediction != "no_prediction")].sort_values("score", ascending=False)
df.rename(columns={"image_id": "id", "preselection_type": "surface_clean", "prediction": "smoothness_clean"}, inplace=True)
s6.create_labelstudio_input_file(df[df.smoothness_clean == smoothness], is_testdata=False, img_path ="experiments", 
                                 output_path=os.path.join(config.data_folder, "experiments", f"exp{exp_id}_embedding_{surface}_{smoothness}_labelstudio.json"))

# sort images
# sanity check: sorted images according to predicted class
origin_folder_path = f"{Path(config.cloud_image_folder).parent}/mapillary_images/training/{img_folder}/osm_tagged"
destination_path = f"{Path(config.cloud_image_folder).parent}/mapillary_images/training/{img_folder}/embedding_selection"

os.makedirs(destination_path, exist_ok=True)
for i in tqdm(range(len(df))):
    img_pred = df.iloc[i]
    image_id = img_pred["id"]
    img_surface = img_pred["surface_clean"]
    img_smoothness = img_pred["smoothness_clean"]

    image_filename = os.path.join(origin_folder_path, f"{image_id}.jpg")
    destination_file_path = os.path.join(destination_path, f"{image_id}.jpg")
    if os.path.exists(image_filename):
        shutil.copy(image_filename, destination_file_path)


utils.crop_frame_for_img_folder(
        f"{config.cloud_image_folder}/training/{img_folder}/embedding_selection/",
        f"{config.cloud_image_folder}/training/{img_folder}/embedding_selection_crop",
    )

