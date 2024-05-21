import os
import shutil
import sys

import pandas as pd
from s6_prepare_manual_annotation import create_labelstudio_input_file

## create new labelstudio file for all images that are misclassified in V9 by the model to check for annotation errors
## This will contribute to V10


sys.path.append("./")
sys.path.append("../")
import config

ds_path = os.path.join(config.cloud_image_folder, "training", "V9")
ds_metadata_path = os.path.join(ds_path, "metadata")
model_pred_path = os.path.join(
    ds_metadata_path,
    "model_predictions/all_train_effnet_surface_quality_prediction-V9_annotated-20240318_130115.csv",
)


##### get prediction and annotations ########
pred = pd.read_csv(model_pred_path, dtype={"Image": str})

# the prediction holds a value for each surface and a class probability. Only keep the highest prob.
idx = pred.groupby("Image")["Prediction"].idxmax()
pred = pred.loc[idx]
pred.rename(
    columns={
        "Image": "image_id",
        "Prediction": "class_prob",
        "Level_0": "surface_pred",
    },
    inplace=True,
)

## annotations
annot = pd.read_csv(
    os.path.join(ds_metadata_path, "annotations_combined.csv"),
    index_col=False,
    dtype={"image_id": str},
)
annot.rename(
    columns={"surface": "surface_true", "smoothness": "quality_label_true"},
    inplace=True,
)
annot["quality_float_true"] = annot["quality_label_true"].map(
    {"excellent": 1, "good": 2, "intermediate": 3, "bad": 4, "very_bad": 5}
)

# annot10 = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V10/metadata/annotations_combined.csv", dtype={"image_id": str})
# check = annot[["image_id", "surface_true"]].merge(annot10[["image_id", "surface"]].set_index("image_id"), how = "left", on="image_id")
df = pred.set_index("image_id").join(
    annot[
        ["image_id", "surface_true", "quality_label_true", "input_version"]
    ].set_index("image_id"),
    how="left",
)

##### identify misclassification ########
misclassified = df[(df.surface_pred != df.surface_true) & (df.surface_true.notna())]
misclassified.reset_index(inplace=True)
with open(os.path.join(ds_metadata_path, "misclassified_surface.txt"), "w") as file:
    for item in misclassified.index.tolist():
        file.write("%s\n" % item)

# store missclassified images in folder
path = os.path.join(ds_metadata_path, "misclassified_images_surface")
os.makedirs(path, exist_ok=True)
for i in range(len(misclassified)):  # len(misclassification)
    img = misclassified.iloc[i]
    img_path = os.path.join(ds_path, "annotated")
    # destination_folder_path = os.path.join(path, img.surface_pred, img.surface_true)
    destination_folder_path = os.path.join(path)
    os.makedirs(destination_folder_path, exist_ok=True)
    destination_path = os.path.join(destination_folder_path, f"{img.image_id}.jpg")
    image_filename = os.path.join(
        img_path, img.surface_true, img.quality_label_true, f"{img.image_id}.jpg"
    )
    shutil.copy(image_filename, destination_path)


# create new labelstudio file and dataset folder
metadata = misclassified
metadata.rename(
    columns={
        "image_id": "id",
        "surface_true": "surface_clean",
        "quality_label_true": "smoothness_clean",
    },
    inplace=True,
)
create_labelstudio_input_file(
    metadata,
    is_testdata=False,
    img_path= config.ds_version,
    output_path=os.path.join(ds_metadata_path, "relabel_misclassified.json"),
    test_city=None,
)
