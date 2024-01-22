import pandas as pd
import sys

# setting path
sys.path.append("./")

import utils
import config

# further filter image selection for training dataset
def select_training_sample():
        metadata = pd.read_csv(
            config.train_image_metadata_with_tags_path.format(config.ds_version)
        )
        # drop potential duplicates
        metadata.drop_duplicates(subset="id", inplace=True)

        metadata["month"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.month
        metadata["hour"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.hour
        metadata = utils.clean_surface(metadata)

        # drop surface specific smoothness
        cleaned_metadata = pd.DataFrame()
        for surface in config.surfaces:
            cleaned_metadata = pd.concat(
                [
                    cleaned_metadata,
                    metadata[
                        (
                            (metadata["surface_clean"] == surface)
                            & (
                                metadata["smoothness"].isin(
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
        metadata = (
            metadata.groupby(["sequence_id"])  # restrict number of images per sequence
            .sample(config.max_img_per_sequence_train, random_state=1, replace=True)
            .drop_duplicates(subset="id")
            .groupby(["tile_id", "surface_clean", "smoothness"])  # restrict number of images per tile (per class)
            .sample(config.max_img_per_tile, random_state=1, replace=True)
            .drop_duplicates(subset="id")

        )

        # alle klassen,die noch nicht imgs_per_class haben, werden mit weiteren highways aufgefüllt
        # prefer pedastrian and cycleway
        metadata_selection = pd.DataFrame()
        for surface in config.surfaces:
            for smoothness in config.surf_smooth_comb[surface]:
                metadata_temp = ((metadata.loc[
                    (
                        (metadata["surface_clean"] == surface)
                        & (metadata["smoothness"] == smoothness)
                        & (metadata["highway"].isin(["pedestrian", "cycleway"]))),])
                .groupby(["surface_clean", "smoothness"])
                .sample(500, random_state=1, replace=True)
                .drop_duplicates(subset="id")
                )
                        
                n_missing_imgs = config.imgs_per_class - len(metadata_temp)
                # fill up to imgs_per_class with other highways
                metadata_fill_temp = (
                    metadata.loc[
                        (
                            (~metadata.id.isin(metadata_temp.id))
                            & (metadata["surface_clean"] == surface)
                            & (metadata["smoothness"] == smoothness),
                        )
                    ]
                )
                n_missing_imgs = n_missing_imgs if n_missing_imgs < len(metadata_fill_temp) else len(metadata_fill_temp)

                metadata_fill_temp = (metadata_fill_temp
                    .sample(n_missing_imgs, random_state=1)
                    .drop_duplicates(subset="id")
                )

                metadata_selection = pd.concat([metadata_selection, metadata_temp, metadata_fill_temp])

        metadata_selection.to_csv(
            config.train_image_selection_metadata_path.format(config.ds_version),
            index=False,
        )

if __name__ == "__main__":
    select_training_sample()