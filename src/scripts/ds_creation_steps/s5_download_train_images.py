import os
import time

import numpy as np
import pandas as pd

import sys
import shutil
import math 

from PIL import Image

# setting path
sys.path.append("./")
sys.path.append("../")

import src.utils as utils
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


def download_training_images(chunk_ids=None, n_per_chunk=100, copy_existing=False):
        folder = config.train_image_folder.format(config.ds_version)
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        if copy_existing:
            chunk_id = chunk_ids[0]
            df=pd.read_csv(config.chunk_img_ids_path.format(config.ds_version, chunk_id, "csv"))
            origin_folder_path = f"/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/"
            destination_folder_path = config.chunk_image_folder.format(config.ds_version, chunk_id)
            
            if not os.path.exists(destination_folder_path):
                os.makedirs(destination_folder_path)

            for i in range(len(df)):
                img_id = df.iloc[i, ]["img_id"]
                if np.isin(img_id, [688027686094143]):
                    continue
                img_chunk = df.iloc[i, ]["chunk_id"]
                destination_path = os.path.join(destination_folder_path, f"{img_id}.jpg")
                origin_path = os.path.join(origin_folder_path, f"{config.ds_version}_c{img_chunk}", "unsorted_images", f"{img_id}.jpg")
                shutil.copy(origin_path, destination_path)

        # Download training images
        else:
            start = time.time()
            if chunk_ids is None:
                metadata = pd.read_csv(
                    config.train_image_selection_metadata_path.format(config.ds_version)
                )

            if not n_per_chunk is None:
                chunk_ids = range(1, math.ceil(len(metadata) / n_per_chunk))

                img_ids_to_download = []
                for chunk_id in chunk_ids:
                    if chunk_id == 0:
                        with open(config.interrater_reliability_img_ids_path.format(config.ds_version, "txt"), "r") as file:
                            img_ids_to_download += [line.strip() for line in file.readlines()]
                    else:
                        with open(config.chunk_img_ids_path.format(config.ds_version, chunk_id, "txt"), "r") as file:
                            img_ids_to_download += [line.strip() for line in file.readlines()]
            else:
                img_ids_to_download = metadata["id"].tolist()

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
    #download_training_images([2], n_per_chunk=None)
    #download_training_images([3], n_per_chunk=None)
    #download_training_images([4], n_per_chunk=None)
    #download_training_images([5], n_per_chunk=None)
    #download_training_images([6], n_per_chunk=None)
    #download_training_images([7], n_per_chunk=None)
    #download_training_images([8], n_per_chunk=None, copy_existing=True)
    
    #download_training_images([1, 2])
    download_training_images(n_per_chunk=None)
