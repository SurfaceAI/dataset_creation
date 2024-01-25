import pandas as pd
#from sklearn.metrics import confusion_matrix
import numpy as np
import pandas as pd
import os
import shutil

path = os.path.join("/", "Users", "alexandra", "Nextcloud-HTW", "SHARED", "SurfaceAI", "data", "mapillary_images", "training", "V4")
files = [
    "00_sample_annotations_edith.csv",
    "00_sample_annotations_esther.csv",
    "00_sample_annotations_alex.csv",
]

df = pd.DataFrame()
for file in files:
    new_file = pd.read_csv(os.path.join(path, "metadata", file))
    df = pd.concat([df, new_file])

df["image_id"] = df.image.apply(
    lambda x: str.split(
        x, "https://freemove.f4.htw-berlin.de/data/local-files/?d=00_sample/"
    )[1]
).apply(lambda x: int(str.split(x, ".jpg")[0]))

# use annotator 1 for first 180 images
df = df.sort_values("annotator").drop_duplicates(subset="image_id", keep="first")

# remove all instances where no surface was annotated
df.loc[df["nostreet"] == '{"choices":[]}', "nostreet"] = None
df.loc[df["nostreet"].notna(), "surface"] = None
df.loc[df["nostreet"].notna(), "smoothness"] = None
df.loc[df["nostreet"].notna(), "roadtype"] = None
# df = df[df["nostreet"].isna()]

# fix "very_bad" / "very bad" (was labeled wihtout "_" initially)
df.loc[df["smoothness"] == "very bad", "smoothness"] = "very_bad"

# df.groupby(["surface", "smoothness"]).size()

df.to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V4/metadata/v4_train_image_sample_annotated_combined.csv")

predictions = pd.read_csv(
    os.path.join(path, "metadata", "v4_train_image_sample_metadata.csv")
)
predictions["highway"] = predictions.highway.str.strip()
predictions.drop("surface", axis=1, inplace=True)
predictions.rename(
    {"surface_clean": "surface_pred", "smoothness": "smoothness_pred"},
    axis=1,
    inplace=True,
)
# predictions.groupby(['surface_clean', 'highway']).size().to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training_data/V4/00_sample/highway_distribution.csv")


predictions_annotations = predictions.set_index("id").join(
    df[["image_id", "surface", "smoothness", "roadtype"]].set_index("image_id"), how="inner"
)
predictions_annotations["combined_label"] = predictions_annotations.surface + "_" + predictions_annotations.smoothness
predictions_annotations["combined_label_pred"] = predictions_annotations.surface_pred + "_" + predictions_annotations.smoothness_pred

# predictions_annotations.reset_index(inplace=True)
# predictions_annotations.rename({"index":"id", "smoothness_pred": "smoothness_osm", "surface_pred":"surface_osm", "highway": "highway_osm", "surface":"surface_annotated", "smoothness":"smoothness_annotated", "roadtype": "highway_annotated"}, axis=1, inplace=True)
# predictions_annotations[["id", "sequence_id", "creator_id", "captured_at", "highway_osm", "surface_osm", "smoothness_osm", "surface_annotated", "smoothness_annotated", "highway_annotated"]].to_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V4/metadata/v4_labels.csv")

surface_cm = predictions_annotations.groupby(["surface", "surface_pred"]).size()
surface_cm = predictions_annotations.groupby(["surface_pred", "surface"]).size()
smoothness_cm = predictions_annotations.groupby(["combined_label", "combined_label_pred"]).size()
#highway_cm = predictions_annotations.groupby(["highway_osm", "highway_annotated"]).size()

# compute accuracy
surface_cm = pd.DataFrame(surface_cm).reset_index().rename({0: "ct"}, axis=1)
smoothness_cm = pd.DataFrame(smoothness_cm).reset_index().rename({0: "ct"}, axis=1)

surface_accuracy = round(100 * (surface_cm[surface_cm.surface == surface_cm.surface_pred].ct.sum() / surface_cm.ct.sum()), 2)
smoothness_accuracy = round(100 * (smoothness_cm[smoothness_cm.combined_label == smoothness_cm.combined_label_pred].ct.sum() / smoothness_cm.ct.sum()), 2)

# accuracy, given the surface is correct
smoothness_accuracy_given_surface = round(100 * (smoothness_cm[smoothness_cm.combined_label == smoothness_cm.combined_label_pred].ct.sum() / surface_cm[surface_cm.surface == surface_cm.surface_pred].ct.sum()), 2)

print(f"surface accuracy: {surface_accuracy}%")
print(f"smoothness accuracy (given all data): {smoothness_accuracy}%")
print(f"smoothness accuracy (given correctly classified surface): {smoothness_accuracy_given_surface}%")

# confusion_matrix(np.array(predictions_annotations.surface[0:10]), np.array(predictions_annotations.surface_pred[0:10]), labels=predictions.surface_pred.unique())

# osm tag counts
# osm_tags = pd.read_csv("/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/osm_tag_counts_germany.csv")
# osm_tags["surface"] = osm_tags.surface.str.strip()
# tag_counts = osm_tags.groupby("surface").sum().sort_values("ct", ascending=False).ct
# tag_counts = pd.DataFrame(tag_counts)
# tag_counts["perc"] = round(tag_counts / tag_counts.sum() * 100)

##### create new folder with annotated images #####

if not os.path.exists(os.path.join(path, "annotated_images")):
    # Create the main directory for sorted images
    output_folder = os.path.join(path, "annotated_images")
    img_folder = os.path.join(path, "images")

    os.makedirs(output_folder, exist_ok=True)

    # Iterate through each row in the DataFrame
    for index, row in df[df.surface.notna()].iterrows():
        # Create subfolder for surface if not exists
        surface_folder = os.path.join(output_folder, row["surface"])
        os.makedirs(surface_folder, exist_ok=True)

        # Create subfolder for smoothness if not exists
        smoothness_folder = os.path.join(surface_folder, row["smoothness"])
        os.makedirs(smoothness_folder, exist_ok=True)

        # Copy the image to the respective folder
        destination_path = os.path.join(smoothness_folder, f"{row['image_id']}.jpg")
        image_filename = os.path.join(img_folder, f"{row['image_id']}.jpg")
        shutil.copy(image_filename, destination_path)

    print("Images sorted successfully.")

    ### not recognizable images into folders

    for index, row in df[df.nostreet.notna()].iterrows():
        if row["nostreet"] == "(mainly) no street visible":
            surface_folder = os.path.join(output_folder, "no_street")
            os.makedirs(surface_folder, exist_ok=True)
        if row["nostreet"] == "surface / smoothness not recognizable":
            surface_folder = os.path.join(output_folder, "not_recognizable")
            os.makedirs(surface_folder, exist_ok=True)

        destination_path = os.path.join(surface_folder, f"{row['image_id']}.jpg")
        image_filename = os.path.join(img_folder, f"{row['image_id']}.jpg")
        shutil.copy(image_filename, destination_path)

else:
    print("Images already annotated and stored. This step is skipped.")