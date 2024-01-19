import pandas as pd

# setting path
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


def prepare_manual_annotation():
    # read and shuffle metadata
    # shuffle images so they are not ordered by surface/smoothness of location
    metadata = (pd
                    .read_csv(config.train_image_selection_metadata_path.format(config.ds_version))
                    .sample(frac=1, random_state=1).reset_index(drop=True)
                )

    # create a file that holds all that image IDs taht should be classified by everyone for interrater reliability
    img_ids_irr = metadata.groupby(["surface_clean", "smoothness"]).sample(
        config.n_irr, random_state=1)["id"].tolist()
    with open(config.interrater_reliability_chunk_ids_path.format(config.ds_version, "txt"), "w") as file:
        for item in img_ids_irr:
            file.write("%s\n" % item)
    create_labelstudio_input_file(metadata[metadata.id.isin(img_ids_irr)], False, 
                                  config.interrater_reliability_chunk_ids_path.format(config.ds_version, "json"))

    # remove irr_chunk_ids from metadata
    metadata = metadata.loc[(~metadata.id.isin(img_ids_irr)),:]

    # create a file for each annotator:
    for i in range(0, config.n_annotators):

        # select fraction of metadata for this annotator
        frac = int(len(metadata) / config.n_annotators)
        metadata_annotator = metadata.iloc[i*frac:(i+1)*frac,:]
        
        # create chunks
        imgids_ann = []
        while len(imgids_ann) < frac:
            md_grouped = (metadata_annotator[~metadata_annotator.id.isin(imgids_ann)] # remove already sampled imgs
                                    .groupby(["surface_clean", "smoothness"]))
            
            # are there enough imgs left to sample from?
            # if yes: sample n_per_chunk
            if all(md_grouped.size() >= config.n_per_chunk):
                imgids_ann += (md_grouped
                                    .sample(config.n_per_chunk, random_state=1)["id"]
                                    .tolist()
                                )
            # if not: take the rest of images for classes below the n chunk size and append them
            else:
                groups_below_chunksize = md_grouped.size()[md_grouped.size() < config.n_per_chunk]
                imgids_ann += (md_grouped
                 .sample(frac=1, random_state=1)
                 .set_index(["surface_clean", "smoothness"])
                 .loc[groups_below_chunksize.index]["id"]
                 .tolist()
                )

        with open(config.annotator_ids_path.format(config.ds_version, i, "txt"), "w") as file:
            for item in imgids_ann:
                file.write("%s\n" % item)
        create_labelstudio_input_file(metadata[metadata.id.isin(imgids_ann)], False, 
                                config.annotator_ids_path.format(config.ds_version, i, "json"))

if __name__=="__main__":
    prepare_manual_annotation()