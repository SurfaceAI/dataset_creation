import os
import time

import pandas as pd

import sys

# setting path
sys.path.append("./")
sys.path.append("../")

import utils
import config

def download_training_images():
        # Download training images
        start = time.time()
        metadata = pd.read_csv(
            config.train_image_selection_metadata_path.format(config.ds_version)
        )

        folder = config.train_image_folder.format(config.ds_version)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # for surface in config.surfaces:
        #     folder = os.path.join(
        #         config.train_image_folder.format(config.ds_version), surface
        #     )
        #     if not os.path.exists(folder):
        #         os.makedirs(folder)

        #     for smoothness in config.surf_smooth_comb[surface]:
                # folder = os.path.join(
                #     config.train_image_folder.format(config.ds_version),
                #     surface,
                #     smoothness,
                # )
                # if not os.path.exists(folder):
                #     os.makedirs(folder)

                # image_ids = list(
                #     metadata[
                #         (metadata["surface_clean"] == surface)
                #         & (metadata["smoothness"] == smoothness)
                #     ]["id"]
                #)
        for i in range(0, len(metadata["id"])):
            if i % 100 == 0:
                print(f"{i} images downloaded")
            utils.download_image(metadata["id"][i], folder)

        # TODO: remove broken images
        print(f"{round((time.time()-start )/ 60)} mins to download all training images")

        # metadata.groupby(['surface_clean', 'smoothness']).size()

if __name__ == "__main__":
    download_training_images()