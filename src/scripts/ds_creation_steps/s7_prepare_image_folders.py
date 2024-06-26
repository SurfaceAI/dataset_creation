import os
import shutil

import pandas as pd

# This script combines all annotated images from different versions and creates folders for the images


def combined_annotations(path, iv, type="concat"):  # types: V4, majority_vote, concat
    path = os.path.join(root_path, iv, "metadata")
    output_path = os.path.join(path, "annotations_combined.csv")

    files = [
        "annotations_a1.csv",
        "annotations_a2.csv",
        "annotations_a3.csv",
    ]
    if iv in ["V5_c2", "V5_c3", "V5_c4"]:
        files = files[0:2]
    elif iv in ["V9"]:
        files = files[0:1]

    df = pd.DataFrame()
    for file in files:
        new_file = pd.read_csv(os.path.join(path, file))
        df = pd.concat([df, new_file])
    df["image_id"] = df.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: int(str.split(x, ".jpg")[0])
    )
    # remove all instances where no surface was annotated
    df.loc[df["nostreet"] == '{"choices":[]}', "nostreet"] = None
    df.loc[df["nostreet"].notna(), "surface"] = None
    df.loc[df["nostreet"].notna(), "smoothness"] = None
    df.loc[df["nostreet"].notna(), "roadtype"] = None
    df["input_version"] = iv
    columns = df.columns

    if type == "V4":
        # use annotator 1 for first 180 images
        df = df.sort_values("annotator").drop_duplicates(
            subset="image_id", keep="first"
        )
        # fix "very_bad" / "very bad" (was labeled wihtout "_" initially)
        df.loc[df["smoothness"] == "very bad", "smoothness"] = "very_bad"

    elif type == "majority_vote":
        mv = (
            df[~df.surface.isna() & ~df.smoothness.isna() & ~df.roadtype.isna()][
                ["image_id", "surface", "smoothness", "roadtype"]
            ]
            .groupby("image_id")
            .agg(lambda x: x.value_counts().index[0])
        )
        df = (
            df.drop(["surface", "smoothness", "roadtype"], axis=1)
            .join(mv, on="image_id")[columns]
            .drop_duplicates(subset="image_id", keep="first")
        )

    elif type == "concat":
        # check if there are any duplicates
        if sum(df.value_counts("image_id") > 1):
            raise ValueError("There are duplicates in the annotations. Please check.")

    df.to_csv(output_path)
    return df


def create_annotated_image_folders(root_path, output_version, df):
    output_folder = os.path.join(root_path, output_version, "annotated")
    os.makedirs(output_folder, exist_ok=True)

    # Iterate through each row in the DataFrame
    for _, row in df[
        df.surface.notna() & df.smoothness.notna() & df.nostreet.isna()
    ].iterrows():
        input_img_folder = os.path.join(
            root_path, row["input_version"], "unsorted_images"
        )

        # Create subfolder for surface if not exists
        surface_folder = os.path.join(output_folder, row["surface"])
        os.makedirs(surface_folder, exist_ok=True)

        # Create subfolder for smoothness if not exists
        smoothness_folder = os.path.join(surface_folder, row["smoothness"])
        os.makedirs(smoothness_folder, exist_ok=True)

        # Copy the image to the respective folder
        destination_path = os.path.join(smoothness_folder, f"{row['image_id']}.jpg")
        image_filename = os.path.join(input_img_folder, f"{row['image_id']}.jpg")
        shutil.copy(image_filename, destination_path)

    ### not recognizable images into folders
    for _, row in df[df.nostreet.notna()].iterrows():
        input_img_folder = os.path.join(
            root_path, row["input_version"], "unsorted_images"
        )
        # in V4, nostreet classification were not yet aligned
        if (row["nostreet"] == "(mainly) no street visible") & (
            row["input_version"] != "V4"
        ):
            surface_folder = os.path.join(output_folder, "no_street")
            os.makedirs(surface_folder, exist_ok=True)
        if row["nostreet"] == "surface / smoothness not recognizable":
            surface_folder = os.path.join(output_folder, "not_recognizable")
            os.makedirs(surface_folder, exist_ok=True)
        if row["nostreet"] == "unsure - please revise":
            surface_folder = os.path.join(output_folder, "revise")
            os.makedirs(surface_folder, exist_ok=True)

        destination_path = os.path.join(surface_folder, f"{row['image_id']}.jpg")
        image_filename = os.path.join(input_img_folder, f"{row['image_id']}.jpg")
        shutil.copy(image_filename, destination_path)


def create_image_folders(output_version, input_versions, root_path):
    all_annotations = pd.DataFrame()
    for iv in input_versions:
        # annotations for each version
        path = os.path.join(root_path, iv, "metadata")

        if iv == "V4":
            annotations = combined_annotations(path, iv, "V4")
        elif iv == "V5_c0":
            annotations = combined_annotations(path, iv, "majority_vote")
        elif iv == "V10":
            annotations = pd.read_csv(
                os.path.join(root_path, "V10", "metadata", "annotations_combined.csv"),
                dtype={"image_id": str},
                index_col=False,
            )
        else:
            annotations = combined_annotations(path, iv, "concat")

        # use image url from previous annotation but label from V9
        if iv == "V9":
            annotations = annotations.drop("input_version", axis=1).merge(
                all_annotations[["image_id", "input_version"]],
                on="image_id",
                how="left",
            )

        all_annotations = pd.concat([all_annotations, annotations])

    # remove duplicates, keep most recent
    all_annotations.drop_duplicates(subset="image_id", keep="last", inplace=True)
    os.makedirs(os.path.join(root_path, output_version, "metadata"), exist_ok=True)

    # for V7, only include asphalt data
    if output_version == "V7":
        all_annotations = all_annotations[all_annotations.surface == "asphalt"]

    all_annotations.to_csv(
        os.path.join(root_path, output_version, "metadata", "annotations_combined.csv"),
        index=False,
    )

    # move images to folders
    create_annotated_image_folders(root_path, output_version, all_annotations)


def update_labels(root_path, output_version, input_version, update_path):
    annotations = pd.read_csv(
        os.path.join(root_path, input_version, "metadata", "annotations_combined.csv"),
        dtype={"image_id": str},
        index_col=False,
    )
    annotations.sort_values("image_id", inplace=True)

    update = pd.read_csv(update_path, dtype={"image_id": str}, index_col=False)
    update["image_id"] = update.image.apply(lambda x: str.split(x, "/")[-1]).apply(
        lambda x: (str.split(x, ".jpg")[0])
    )
    update.sort_values("image_id", inplace=True)

    annotations.loc[annotations.image_id.isin(update.image_id), "nostreet"] = update[
        "nostreet"
    ].values
    annotations.loc[annotations.image_id.isin(update.image_id), "surface"] = update[
        "surface"
    ].values
    annotations.loc[annotations.image_id.isin(update.image_id), "smoothness"] = update[
        "smoothness"
    ].values

    os.makedirs(os.path.join(root_path, output_version), exist_ok=True)
    os.makedirs(os.path.join(root_path, output_version, "metadata"), exist_ok=True)
    annotations.to_csv(
        os.path.join(root_path, output_version, "metadata", "annotations_combined.csv"),
        index=False,
    )
    create_annotated_image_folders(root_path, output_version, annotations)


if __name__ == "__main__":
    output_version = "V12"
    input_versions = ["V11"]
    root_path = os.path.join(
        "/",
        "Users",
        "alexandra",
        "Nextcloud-HTW",
        "SHARED",
        "SurfaceAI",
        "data",
        "mapillary_images",
        "training",
    )
    # create_image_folders(output_version, input_versions, root_path)

    update_path = os.path.join(
        root_path, "V11", "re-classify", "updated_pavingstones_annotations.csv"
    )
    update_labels(root_path, output_version, input_versions[0], update_path)
