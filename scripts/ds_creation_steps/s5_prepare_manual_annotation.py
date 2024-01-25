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


def prepare_manual_annotation(chunk_ids=None):
    # read and shuffle metadata
    # shuffle images so they are not ordered by surface/smoothness of location
    chunks_folder = config.chunks_folder.format(config.ds_version)
    if not os.path.exists(chunks_folder):
        os.makedirs(chunks_folder)

    metadata = (pd
                    .read_csv(config.train_image_selection_metadata_path.format(config.ds_version), dtype={"id": str})
                    .sample(frac=1, random_state=1).reset_index(drop=True)
                )

    if (chunk_ids is None) or (0 in chunk_ids):
        # create a file that holds all that image IDs taht should be classified by everyone for interrater reliability
        img_ids_irr = metadata.groupby(["surface_clean", "smoothness_clean"]).sample(
            config.n_irr, random_state=1)["id"].tolist()
        with open(config.interrater_reliability_img_ids_path.format(config.ds_version, "txt"), "w") as file:
            for item in img_ids_irr:
                file.write("%s\n" % item)
        create_labelstudio_input_file(metadata[metadata.id.isin(img_ids_irr)], False, 
                                    config.interrater_reliability_img_ids_path.format(config.ds_version, "json"))

    
    if (chunk_ids is None) or (max(chunk_ids) > 0):
        if chunk_ids is None:
            chunk_ids = range(1, math.ceil(len(metadata) / config.n_per_chunk))
        else:
            chunk_ids = [x for x in chunk_ids if x > 0]

        # remove irr_chunk_ids from metadata
        with open(config.interrater_reliability_img_ids_path.format(config.ds_version, "txt"), "r") as file:
            img_ids_irr = [line.strip() for line in file.readlines()]
        metadata = metadata.loc[(~metadata.id.isin(img_ids_irr)),:]

        # remove ids used in previous chunks
        # TODO

        for chunk_id in chunk_ids:
            # create a file for each annotator - and chunk?:
            for i in range(0, config.n_annotators):

                # # select fraction of metadata for this annotator
                # frac = int(len(metadata) / config.n_annotators)
                # metadata_annotator = metadata.iloc[i*frac:(i+1)*frac,:]
                
                # create chunks
                imgids_ann = []
                #while len(imgids_ann) < frac:
                md_grouped = (metadata.groupby(["surface_clean", "smoothness_clean"]))
                
                # are there enough imgs left to sample from?
                # if not: take the rest of images for classes below the n chunk size and append them
                groups_below_chunksize = md_grouped.size()[md_grouped.size() < config.n_per_chunk]
                if len(groups_below_chunksize) > 0:
                    imgids_ann += (md_grouped
                    .sample(frac=1, random_state=1)
                    .set_index(["surface_clean", "smoothness_clean"])
                    .loc[groups_below_chunksize.index]["id"]
                    .tolist()
                    )

                # then append the chunk size for the remaining classes
                groups_in_chunksize = md_grouped.size()[md_grouped.size() >= config.n_per_chunk]

                imgids_ann += (metadata
                    .set_index(["surface_clean", "smoothness_clean"])
                    .loc[groups_in_chunksize.index]
                    .groupby(["surface_clean", "smoothness_clean"])
                    .sample(config.n_per_chunk, random_state=1)["id"]
                    .tolist()
                )
                
                with open(config.annotator_ids_path.format(config.ds_version, chunk_id, i, "txt"), "w") as file:
                    for item in imgids_ann:
                        file.write("%s\n" % item)
                create_labelstudio_input_file(metadata[metadata.id.isin(imgids_ann)], False, 
                                        config.annotator_ids_path.format(config.ds_version, chunk_id, i, "json"))

                # remove used images
                metadata = metadata.loc[(~metadata.id.isin(imgids_ann)),:]

if __name__=="__main__":
    prepare_manual_annotation(chunk_ids=[1])