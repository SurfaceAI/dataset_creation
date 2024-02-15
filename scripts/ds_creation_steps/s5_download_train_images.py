import os
import time

import pandas as pd

import sys
import math 

from PIL import Image

# setting path
sys.path.append("./")
sys.path.append("../")

import utils
import config

def delete_broken_images(folder_path, threshold_size_kb=1):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if the file is an image 
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            try:
                # try opening the image
                Image.open(file_path)
            except Exception as e:
                os.remove(file_path)


def download_training_images(chunk_ids=None, n_per_chunk=100):
        folder = config.train_image_folder.format(config.ds_version)
        if not os.path.exists(folder):
            os.makedirs(folder)
        # Download training images
        start = time.time()
        if chunk_ids is None:
            metadata = pd.read_csv(
                config.train_image_selection_metadata_path.format(config.ds_version)
            )
            chunk_ids = range(1, math.ceil(len(metadata) / n_per_chunk))

        img_ids_to_download = []
        for chunk_id in chunk_ids:
            if chunk_id == 0:
                with open(config.interrater_reliability_img_ids_path.format(config.ds_version, "txt"), "r") as file:
                    img_ids_to_download += [line.strip() for line in file.readlines()]
            else:
                with open(config.chunk_img_ids_path.format(config.ds_version, chunk_id, "txt"), "r") as file:
                    img_ids_to_download += [line.strip() for line in file.readlines()]

            folder = config.chunk_image_folder.format(config.ds_version, chunk_id)
            if not os.path.exists(folder):
                os.makedirs(folder)

            for i in range(0, len(img_ids_to_download)):
                if i % 100 == 0:
                    print(f"{i} images downloaded")
                utils.download_image(img_ids_to_download[i], folder)

            # remove broken images 
            delete_broken_images(folder)

        print(f"{round((time.time()-start )/ 60)} mins to download all training images")

        # metadata.groupby(['surface_clean', 'smoothness']).size()

if __name__ == "__main__":
    #download_training_images([0,1])
    download_training_images([2], n_per_chunk=None)