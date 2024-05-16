import os
import shutil
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import config

# sort images into folders, only if predicted surfaces matches OSM surface

ds_version = "v200"

pred_file = config.model_prediction_file[ds_version]
df = pd.read_csv(
    os.path.join(
        config.model_prediction_path.format(ds_version), "model_predictions", pred_file
    ),
    dtype={"Image": str},
)
idx = df.groupby("Image")["Prediction"].idxmax()
df = df.loc[idx]
metadata_path = config.train_image_selection_metadata_path.format(ds_version)
metadata = pd.read_csv(metadata_path, dtype={"id": str})

ds_version_folder_path = os.path.join(config.cloud_image_folder, "training", ds_version)
#origin_folder_path = os.path.join(ds_version_folder_path, "unsorted_images")
origin_folder_path = os.path.join("data", ds_version, "train_images")
for i in tqdm(range(len(df))):
    img_pred = df.iloc[i]
    image_id = img_pred["Image"]
    img = metadata[metadata["id"] == image_id]
    destination_path = os.path.join(
        ds_version_folder_path,
        img_pred.Level_0
    )
    os.makedirs(destination_path, exist_ok=True)
    image_filename = os.path.join(origin_folder_path, f"{image_id}.jpg")
    destination_path = os.path.join(destination_path, f"{image_id}.jpg")
    if os.path.exists(image_filename):
        shutil.copy(image_filename, destination_path)
