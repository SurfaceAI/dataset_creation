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

# prepare labeling of all of v101 for experiment 1 (only label true / false)

v101 = pd.read_csv(f"{config.cloud_image_folder}/automated_labeling_experiments/annotations_combined/V101.csv")
v101["image_id"] = v101.image.apply(
    lambda x: str.split(
        x, "https://freemove.f4.htw-berlin.de/data/local-files/?d=experiments/"
    )[1]
).apply(lambda x: str.split(x, ".jpg")[0])

exp_0 = pd.read_csv(f"{config.cloud_image_folder}/automated_labeling_experiments/gpt_experiments/results/experiment_1_V101_asphalt_bad.csv", dtype={"image_id": str})
exp_1 = pd.read_csv(f"{config.cloud_image_folder}/automated_labeling_experiments/gpt_experiments/results/experiment_1_V101_paving_stones_intermediate.csv", dtype={"image_id": str})
exp_2 = pd.read_csv(f"{config.cloud_image_folder}/automated_labeling_experiments/gpt_experiments/results/experiment_1_V101_paving_stones_bad.csv", dtype={"image_id": str})
exp_images = pd.concat([exp_0, exp_1, exp_2])
df = exp_images[~exp_images.image_id.isin(v101.image_id)]

# only keep relevant classes
df = df[((df.preselection_type == "asphalt") & (df.preselection_quality == "bad"))|
        (df.preselection_type == "paving_stones") & (df.preselection_quality == "bad") |
        (df.preselection_type == "paving_stones") & (df.preselection_quality == "intermediate") ]

df.rename(columns={"image_id": "id", "preselection_type": "surface_clean", "preselection_quality": "smoothness_clean"}, inplace=True)
s6.create_labelstudio_input_file(df, is_testdata=False, img_path ="experiments", 
                                 output_path=os.path.join(config.data_folder, "experiments", f"exp1_remaining_images.json"))


# sort images
# sanity check: sorted images according to predicted class
destination_path = f"{config.cloud_image_folder}/training/V101/batch_3"
os.makedirs(destination_path, exist_ok=True)

for i in tqdm(range(len(df))):
    img_pred = df.iloc[i]
    image_id = img_pred["id"]
    img_surface = img_pred["surface_clean"]
    img_smoothness = img_pred["smoothness_clean"]
    img_folder = f"V101/{img_surface}/{img_smoothness}"
    origin_folder_path = f"{config.cloud_image_folder}/training/V101/unsorted_images"

    image_filename = os.path.join(origin_folder_path, f"{image_id}.jpg")
    destination_file_path = os.path.join(destination_path, f"{image_id}.jpg")
    if os.path.exists(image_filename):
        shutil.copy(image_filename, destination_file_path)


utils.crop_frame_for_img_folder(
        destination_path,
        f"{config.cloud_image_folder}/training/V101/batch_3_crop",
    )

