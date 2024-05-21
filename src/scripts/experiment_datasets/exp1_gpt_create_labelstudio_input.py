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

surface = "asphalt"
smoothness = "intermediate"

# ashpalt bad results
df = pd.read_csv(os.path.join(Path(config.cloud_image_folder).parent, "labeling", "image_annotation", "gpt_experiments", "results", f"experiment_1_V101_{surface}_{smoothness}.csv"))
df.rename(columns={"image_id": "id", "preselection_type": "surface_clean", "prediction": "smoothness_clean"}, inplace=True)
s6.create_labelstudio_input_file(df[df.smoothness_clean == smoothness], is_testdata=False, img_path ="experiments", 
                                 output_path=os.path.join(config.data_folder, "experiments", f"exp1_gpt_{surface}_{smoothness}_labelstudio.json"))

# sort images
# sanity check: sorted images according to predicted class
origin_folder_path = f"/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V101/{surface}/{smoothness}/osm_tagged"
destination_path = f"/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V101/{surface}/{smoothness}/sorted"

for i in tqdm(range(len(df))):
    img_pred = df.iloc[i]
    image_id = img_pred["id"]
    img_surface = img_pred["surface_clean"]
    img_smoothness = img_pred["smoothness_clean"]

    image_filename = os.path.join(origin_folder_path, f"{image_id}.jpg")
    os.makedirs(os.path.join(destination_path, img_surface, img_smoothness), exist_ok=True)
    destination_file_path = os.path.join(destination_path, img_surface, img_smoothness, f"{image_id}.jpg")
    if os.path.exists(image_filename):
        shutil.copy(image_filename, destination_file_path)


utils.crop_frame_for_img_folder(
        f"/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V101/{surface}/{smoothness}/sorted/{surface}/{smoothness}/",
        f"/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V101/{surface}/{smoothness}/selection_crop",
    )

