import math
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent.parent))

import config
import constants as const
import utils as utils


# further filter image selection for training dataset
def select_training_sample():
    metadata = pd.read_csv(
        config.train_image_metadata_with_tags_path.format(config.ds_version),
        dtype={"id": str},
    )
    # drop potential duplicates
    metadata.drop_duplicates(subset="id", inplace=True)

    # metadata["month"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.month
    # metadata["hour"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.hour
    metadata = utils.clean_surface(metadata)

    metadata = utils.clean_smoothness(metadata)

    # drop surface specific smoothness
    # TODO: neater way of implementing?
    cleaned_metadata = pd.DataFrame()
    for surface in config.surfaces:
        cleaned_metadata = pd.concat(
            [
                cleaned_metadata,
                metadata[
                    (
                        (metadata["surface_clean"] == surface)
                        & (
                            metadata["smoothness_clean"].isin(
                                config.surf_smooth_comb[surface]
                            )
                        )
                    )
                ],
            ]
        )
    metadata = cleaned_metadata

    # remove already labeled images
    with open(config.labeled_imgids_path, "r") as file:
        already_labled_ids = file.read().splitlines()
    metadata = metadata[~metadata.id.isin(already_labled_ids)]

    # filter date (outdated)
    # metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]
    # not in winter (bc of snow)
    # metadata = metadata[metadata["month"].isin(range(3,11))]
    # not at night (bc of bad light)
    # metadata = metadata[metadata["hour"].isin(range(8,18))]

    # remove panorama images
    metadata = metadata[metadata["is_pano"] == "f"]
    # remove Autobahn images
    metadata = metadata[~metadata["highway"].isin(["motorway", "motorway_link"])]

    # filtering by max_img_per_sequence and max_img_per_tile reduces df from 13 mio to 50k images
    # sample x images per class
    # metadata = (
    #     metadata.groupby(["sequence_id"])  # restrict number of images per sequence
    #     .sample(config.max_img_per_sequence_train, random_state=1, replace=True)
    #     .drop_duplicates(subset="id")
    #     .groupby(["tile_id", "surface_clean", "smoothness_clean"])  # restrict number of images per tile (per class)
    #     .sample(config.max_img_per_tile, random_state=1, replace=True)
    #     .drop_duplicates(subset="id")

    # )

    # alle klassen,die noch nicht imgs_per_class haben, werden mit weiteren highways aufgefüllt
    # prefer pedastrian and cycleway
    metadata_selection = pd.DataFrame()
    for surface in config.surfaces:
        for smoothness in config.surf_smooth_comb[surface]:
            metadata_class = metadata.loc[
                (
                    (metadata["surface_clean"] == surface)
                    & (metadata["smoothness_clean"] == smoothness)
                )
            ]

            # sample by sequence_id and tile_id
            metadata_class = (
                metadata_class.groupby(
                    ["sequence_id"]
                )  # restrict number of images per sequence
                .sample(config.max_img_per_sequence_train, random_state=1, replace=True)
                .drop_duplicates(subset="id")
                .groupby(
                    ["tile_id", "surface_clean", "smoothness_clean"]
                )  # restrict number of images per tile (per class)
                .sample(config.max_img_per_tile, random_state=1, replace=True)
                .drop_duplicates(subset="id")
            )

            # prefer pedestrian and cycleway, take sample of 500
            metadata_temp = (
                (
                    metadata_class.loc[
                        (metadata_class["highway"].isin(["pedestrian", "cycleway"])),
                    ]
                )
                .groupby(["surface_clean", "smoothness_clean"])
                .sample(500, random_state=1, replace=True)
                .drop_duplicates(subset="id")
            )

            n_missing_imgs = config.imgs_per_class - len(metadata_temp)
            # fill up to imgs_per_class with other highways
            metadata_fill_temp = metadata_class.loc[
                ((~metadata_class["id"].isin(metadata_temp["id"])))
            ]
            # compute how many images are missing OR how many images are available
            # (otherwise, if a higher number than available is used in "sample", function gives an error)
            n_missing_imgs = (
                n_missing_imgs
                if n_missing_imgs < len(metadata_fill_temp)
                else len(metadata_fill_temp)
            )

            metadata_fill_temp = metadata_fill_temp.sample(
                n_missing_imgs, random_state=1
            )

            # combine: selection from previous class, pedestrian/cycleway sample, other (filled up) sample
            metadata_selection = pd.concat(
                [metadata_selection, metadata_temp, metadata_fill_temp]
            )

    metadata_selection.to_csv(
        config.train_image_selection_metadata_path.format(config.ds_version),
        index=False,
    )


# different ways of defining sizes: either n_per_chunk, which gives an even number of images for each class and annotator
# other option to specificially define size_per_class, which is a dict that says the number of images to be sampled for each class
def create_chunks(
    chunk_ids,
    n_per_chunk=100,
    selected_surface=None,
    selected_smoothness=None,
    filtered_out=False,
    filtered_out_perc=None,
):
    # read and shuffle metadata
    # shuffle images so they are not ordered by surface/smoothness of location
    chunks_folder = config.chunks_folder.format(config.ds_version)
    if not os.path.exists(chunks_folder):
        os.makedirs(chunks_folder)

    metadata = (
        pd.read_csv(
            config.train_image_selection_metadata_path.format(config.ds_version),
            dtype={"id": str},
        )
        .sample(frac=1, random_state=1)
        .reset_index(drop=True)  # make random order
    )

    # chunk to get a share of filtered out images to counteract bias
    if filtered_out:
        chunk_id = chunk_ids[0]
        filtered_img_ids = []
        c_ids = []
        for c in [1, 2, 3, 4, 7]:
            with open(
                config.chunk_filtered_img_ids_path.format(config.ds_version, c, "txt"),
                "r",
            ) as file:
                ids = [line.strip() for line in file.readlines()]
                filtered_img_ids += ids
                c_ids += [c for _ in range(len(ids))]

        filtered_imgs = pd.DataFrame(
            {"chunk_id": c_ids, "img_id": filtered_img_ids}
        ).sample(frac=filtered_out_perc, random_state=1)
        filtered_imgs.to_csv(
            config.chunk_img_ids_path.format(config.ds_version, chunk_id, "csv"),
            index=False,
        )

        with open(
            config.chunk_img_ids_path.format(config.ds_version, chunk_id, "txt"), "w"
        ) as file:
            for item in filtered_imgs["img_id"]:
                file.write("%s\n" % item)

    else:
        if (chunk_ids is None) or (0 in chunk_ids):
            # create a file that holds all that image IDs that should be classified by everyone for interrater reliability
            img_ids_irr = (
                metadata.groupby(["surface_clean", "smoothness_clean"])
                .sample(config.n_irr, random_state=1)["id"]
                .tolist()
            )
            with open(
                config.interrater_reliability_img_ids_path.format(
                    config.ds_version, "txt"
                ),
                "w",
            ) as file:
                for item in img_ids_irr:
                    file.write("%s\n" % item)

        if (chunk_ids is None) or (max(chunk_ids) > 0):
            if chunk_ids is None:
                chunk_ids = range(1, math.ceil(len(metadata) / n_per_chunk))
            else:
                chunk_ids = [x for x in chunk_ids if x > 0]

            # remove ids that have previously been labeled
            with open(config.labeled_imgids_path, "r") as file:
                already_labled_ids = file.read().splitlines()
            metadata = metadata[~metadata.id.isin(already_labled_ids)]

            # remove irr_chunk_ids from metadata
            if os.path.exists(
                config.interrater_reliability_img_ids_path.format(
                    config.ds_version, "txt"
                )
            ):
                with open(
                    config.interrater_reliability_img_ids_path.format(
                        config.ds_version, "txt"
                    ),
                    "r",
                ) as file:
                    img_ids_irr = [line.strip() for line in file.readlines()]
                metadata = metadata.loc[(~metadata.id.isin(img_ids_irr)), :]

            # remove images from previous chunks
            if min(chunk_ids) > 1:
                for i in range(1, min(chunk_ids)):
                    with open(
                        config.chunk_img_ids_path.format(config.ds_version, i, "txt"),
                        "r",
                    ) as file:
                        already_labled_ids = file.read().splitlines()
                    metadata = metadata[~metadata.id.isin(already_labled_ids)]

            # select surface and smoothness
            if selected_surface is not None:
                metadata = metadata[metadata.surface_clean.isin(selected_surface)]
            if selected_smoothness is not None:
                metadata = metadata[
                    metadata.smoothness_clean.isin(selected_smoothness.keys())
                ]

            if n_per_chunk is not None:
                for chunk_id in chunk_ids:
                    # create a txt file for each chunk

                    # if n_per_chunk is none, then include all images
                    # else, sample according to chunk_size
                    chunk_imgids = []
                    md_grouped = metadata.groupby(["surface_clean", "smoothness_clean"])
                    # are there enough imgs left to sample from?
                    # if not: take the rest of images for classes below the n chunk size and append them
                    groups_below_chunksize = md_grouped.size()[
                        md_grouped.size() < (n_per_chunk * config.n_annotators)
                    ]
                    if len(groups_below_chunksize) > 0:
                        chunk_imgids += (
                            md_grouped.sample(frac=1, random_state=1)
                            .set_index(["surface_clean", "smoothness_clean"])
                            .loc[groups_below_chunksize.index]["id"]
                            .tolist()
                        )

                    # then append the chunk size for the remaining classes
                    groups_in_chunksize = md_grouped.size()[
                        md_grouped.size() >= (n_per_chunk * config.n_annotators)
                    ]

                    chunk_imgids += (
                        metadata.set_index(["surface_clean", "smoothness_clean"])
                        .loc[groups_in_chunksize.index]
                        .groupby(["surface_clean", "smoothness_clean"])
                        .sample((n_per_chunk * config.n_annotators), random_state=1)[
                            "id"
                        ]
                        .tolist()
                    )
            elif selected_smoothness is not None:
                chunk_id = chunk_ids[0]
                chunk_imgids = []
                for smoothness, size in selected_smoothness.items():
                    if size is None:
                        # take all images
                        chunk_imgids += metadata[
                            metadata.smoothness_clean == smoothness
                        ]["id"].tolist()

                    else:
                        # sample according to defined size
                        chunk_imgids += (
                            metadata[metadata.smoothness_clean == smoothness]
                            .sample(size, random_state=1)["id"]
                            .tolist()
                        )

            else:
                chunk_imgids = metadata["id"].tolist()
                chunk_id = chunk_ids[0]

        with open(
            config.chunk_img_ids_path.format(config.ds_version, chunk_id, "txt"), "w"
        ) as file:
            for item in chunk_imgids:
                file.write("%s\n" % item)


if __name__ == "__main__":
    # v5
    # select_training_sample()
    # create_chunks([1], n_per_chunk=100)
    # chunk 2 only consists of asphalt intermediate and bad
    # create_chunks([2], n_per_chunk=None, selected_surface=[const.ASPHALT], selected_smoothness=[const.INTERMEDIATE, const.BAD])
    # create_chunks([3], n_per_chunk=None, selected_surface=[const.PAVING_STONES],
    #              selected_smoothness={const.EXCELLENT: 800, const.INTERMEDIATE: 800, const.BAD: None})
    # create_chunks([4], n_per_chunk=None, selected_surface=[const.PAVING_STONES],
    #            selected_smoothness={const.EXCELLENT: None, const.INTERMEDIATE: None})
    # create_chunks([5], n_per_chunk=None, selected_surface=[const.SETT],
    #            selected_smoothness={const.BAD: None, const.GOOD: None})
    # create_chunks([6], n_per_chunk=None, selected_surface=[const.CONCRETE],
    #             selected_smoothness={const.BAD: None, const.EXCELLENT: None, const.INTERMEDIATE: 200})
    # create_chunks([7], n_per_chunk=None, selected_surface=[const.UNPAVED],
    #        selected_smoothness={const.VERY_BAD: 300, const.BAD: 50, const.INTERMEDIATE: 50})
    # create_chunks([8], n_per_chunk=None, filtered_out = True, filtered_out_perc=0.1)
    # create_chunks([9], n_per_chunk=None)
    create_chunks([9], n_per_chunk=None)

    # v100
    # select_training_sample()
    # create_chunks([1], n_per_chunk=None, selected_surface=[const.ASPHALT],
    #               selected_smoothness={const.INTERMEDIATE: None, const.BAD: None})
    # create_chunks([2], n_per_chunk=None, selected_surface=[const.PAVING_STONES],
    #               selected_smoothness={const.EXCELLENT: None, const.INTERMEDIATE: None, const.BAD: None})

    # V101
    # extra script: v101.py
    create_chunks(
        [1],
        n_per_chunk=None,
        selected_surface=[const.ASPHALT],
        selected_smoothness={const.INTERMEDIATE: None, const.BAD: None},
    )
    create_chunks(
        [2],
        n_per_chunk=None,
        selected_surface=[const.PAVING_STONES],
        selected_smoothness={
            const.EXCELLENT: None,
            const.INTERMEDIATE: None,
            const.BAD: None,
        },
    )

    # V200
    # extra script v200.py
