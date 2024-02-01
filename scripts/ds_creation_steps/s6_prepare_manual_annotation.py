import pandas as pd

# setting path
import os
import sys
import json 
import math

sys.path.append("./")
import config
import utils


def training_entity(row, img_folder):
    return {
        "data": {"image": f"{img_folder}/{row['id']}.jpg"},
        "predictions": [
            {
                "result": [
                    {
                        "from_name": "surface",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [row["surface_clean"]]},
                    },
                    {
                        "from_name": "smoothness",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [row["smoothness"]]},
                    },
                ]
            }
        ],
    }


def test_entity(row, img_folder):
    entity = {"data": {"image": f"{img_folder}/{row['id']}.jpg"}}

    # only add predictions if there is a surface, otherwise error from labelstudio
    if isinstance(row["surface_clean"], str):
        entity["predictions"] = [
            {
                "result": [
                    {
                        "from_name": "surface",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [row["surface_clean"]]},
                    },
                    {
                        "from_name": "smoothness",
                        "to_name": "image",
                        "type": "choices",
                        "value": {"choices": [row["smoothness"]]},
                    },
                ]
            }
        ]
    return entity


def create_labelstudio_input_file(metadata, is_testdata, output_path):
    img_url =  config.labelstudio_absolute_path.format(config.ds_version)

    # Convert each row to JSON object and collect them in a list
    json_data = []
    for _, row in metadata.iterrows():
        if is_testdata:
            entity = test_entity(row, img_url)
        else:
            entity = training_entity(row, img_url)
        json_data.append(entity)

    result_json_str = json.dumps(json_data, indent=2)

    # Write JSON string to a file
    with open(output_path, "w") as file:
        file.write(result_json_str)


# filter to only include images with confident surface prediction
def filter_by_model_prediction(metadata, chunk_id):
    model_prediction = pd.read_csv(config.model_prediction_path.format(config.ds_version, config.ds_version, chunk_id), dtype={"image_id": str})   


    df = (metadata
     .set_index("id")
     .join(model_prediction.set_index("image_id"), how="left")
    )
    df["combined_prediction"] = "no prediction"
    df.loc[df.model_prediction == df.surface_clean, "combined_prediction"] = df[df.model_prediction == df.surface_clean].surface_clean

    with open(config.chunk_filtered_img_ids_path.format(config.ds_version, chunk_id, "txt"), "w") as file:
        for item in df[df.combined_prediction == "no prediction"].index.tolist():
            file.write("%s\n" % item)

    return (df[df.combined_prediction != "no prediction"].index.tolist())

def prepare_manual_annotation(chunk_ids=None):
    # read and shuffle metadata
    # shuffle images so they are not ordered by surface/smoothness of location
    metadata = (pd
                    .read_csv(config.train_image_selection_metadata_path.format(config.ds_version), dtype={"id": str})
                    .sample(frac=1, random_state=1).reset_index(drop=True)
                )

    if chunk_ids is None:
        chunk_ids = range(1, math.ceil(len(metadata) / config.n_per_chunk))

    for chunk_id in chunk_ids:
        if chunk_id == 0:
            with open(config.interrater_reliability_img_ids_path.format(config.ds_version, "txt"), "r") as file:
                chunk_img_ids = file.read().splitlines()
            create_labelstudio_input_file(metadata[metadata.id.isin(chunk_img_ids)].sort_values(["surface_clean", "smoothness_clean"]),
                                        False, config.interrater_reliability_img_ids_path.format(config.ds_version, "json_path"))
        
        else:
            # get metadata for chunk imgs
            with open(config.chunk_img_ids_path.format(config.ds_version, chunk_id, "txt"), "r") as file:
                chunk_img_ids = file.read().splitlines()

            filtered_chunk_img_ids = filter_by_model_prediction(metadata[metadata.id.isin(chunk_img_ids)], chunk_id)
            chunk_metadata = metadata[metadata.id.isin(filtered_chunk_img_ids)]

            md_grouped = (chunk_metadata
                            .groupby(["surface_clean", "smoothness_clean"]))
            
            # give a third of each group to each annotator
            for i in range(0, config.n_annotators):
                # create chunks
                imgids_ann = []
                #while len(imgids_ann) < frac:
                
                for label in md_grouped.size().index:
                    count = md_grouped.size()[label]
                    chunk_size = math.floor(count / config.n_annotators)

                    imgids_ann += (chunk_metadata[
                        (chunk_metadata.surface_clean == label[0]) & (chunk_metadata.smoothness_clean == label[1])
                        ]
                    .sample(chunk_size, random_state=1)["id"]
                    .tolist()
                    )
                
                chunk_metadata = chunk_metadata[~chunk_metadata.id.isin(imgids_ann)]

                with open(config.annotator_ids_path.format(config.ds_version, chunk_id, i, "txt"), "w") as file:
                    for item in imgids_ann:
                        file.write("%s\n" % item)
                # group according to surface and smoothness for labelstudio
                create_labelstudio_input_file(metadata[metadata.id.isin(imgids_ann)].sort_values(["surface_clean", "smoothness_clean"]), False, 
                                        config.annotator_ids_path.format(config.ds_version, chunk_id, i, "json"))


if __name__=="__main__":
    prepare_manual_annotation(chunk_ids=[1])


