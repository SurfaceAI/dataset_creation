import os
import sys
import shutil
import pandas as pd

## create new labelstudio file for all images that are misclassified in V9 by the model to check for annotation errors
## This will contribute to V12


from s6_prepare_manual_annotation import create_labelstudio_input_file
sys.path.append("./")
sys.path.append("../")
import config
import constants as const

pred_files = {const.PAVING_STONES: "all_train_paving_stones_prediction-V11_annotated_paving_stones-20240417_094244.csv"}
output_name = "misclassified_paving_stone_quality"
ds_path = os.path.join(config.cloud_image_folder, "training", "V11")
ds_metadata_path = os.path.join(ds_path, "metadata")
model_pred_path = os.path.join(ds_metadata_path, "model_predictions", pred_files[const.PAVING_STONES])


##### get prediction and annotations ########
pred = pd.read_csv(model_pred_path, dtype={"Image": str}) 
pred.rename(columns={"Image": "image_id"}, inplace=True)

## annotations
annot = pd.read_csv(os.path.join(ds_metadata_path, "annotations_combined.csv"), index_col=False, dtype={"image_id": str})
annot.rename(columns={"surface": "surface_true", "smoothness": "quality_label_true"}, inplace=True)
annot["quality_float_true"] = annot["quality_label_true"].map({"excellent": 1, "good": 2, "intermediate": 3, "bad": 4, "very_bad": 5})

df = pred.set_index("image_id").join(annot[["image_id", "surface_true", "quality_float_true", "quality_label_true", "input_version"]].set_index("image_id"), how="left")

##### identify misclassification (diff larger than 1) ########
misclassified = df[((df.quality_float_true - df.Prediction) > 1 & (df.surface_true.notna()))]
misclassified.reset_index(inplace=True)
with open(os.path.join(ds_metadata_path, f"{output_name}.txt"), "w") as file:
    for item in misclassified.index.tolist():
        file.write("%s\n" % item)

# store missclassified images in folder
path = os.path.join(ds_metadata_path, output_name)
os.makedirs(path, exist_ok=True)
for i in range(len(misclassified)):  # len(misclassification)
    img = misclassified.iloc[i]
    img_path = os.path.join(ds_path, "annotated")
    #destination_folder_path = os.path.join(path, img.surface_pred, img.surface_true)
    destination_folder_path = os.path.join(path)
    os.makedirs(destination_folder_path, exist_ok=True)
    destination_path = os.path.join(destination_folder_path, f"{img.image_id}.jpg")
    image_filename = os.path.join(img_path, img.surface_true, img.quality_label_true, f"{img.image_id}.jpg")
    shutil.copy(image_filename, destination_path)


#### reclassify all images for GPT experiment ####
gpt_imgs = pd.read_csv(os.path.join(config.cloud_image_folder.split("/mapillary_images")[0], "labeling", "gpt_experiments", "images_pre_experiment_paving_stones.csv"), dtype={"image_id": str})
gpt_imgs = df[df.index.isin(gpt_imgs.image_id)]
gpt_imgs.reset_index(inplace=True)

# store missclassified images in folder
path = os.path.join(ds_metadata_path, "gpt_experiment")
os.makedirs(path, exist_ok=True)
for i in range(len(gpt_imgs)):  # len(misclassification)
    img = gpt_imgs.iloc[i]
    img_path = os.path.join(ds_path, "annotated")
    #destination_folder_path = os.path.join(path, img.surface_pred, img.surface_true)
    destination_folder_path = os.path.join(path)
    os.makedirs(destination_folder_path, exist_ok=True)
    destination_path = os.path.join(destination_folder_path, f"{img.image_id}.jpg")
    image_filename = os.path.join(img_path, img.surface_true, img.quality_label_true, f"{img.image_id}.jpg")
    shutil.copy(image_filename, destination_path)


# create new labelstudio file and dataset folder
metadata = pd.concat([gpt_imgs, misclassified]).drop_duplicates("image_id")
metadata.rename(columns={"image_id": "id", "surface_true": "surface_clean", "quality_label_true": "smoothness_clean"}, inplace=True)
create_labelstudio_input_file(metadata, is_testdata=False, output_path=os.path.join(ds_metadata_path, f"{output_name}.json"), test_city=None)