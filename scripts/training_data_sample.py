import pandas as pd
import json

# setting path
import sys
sys.path.append('./')
import config
import constants as const

metadata_path = config.train_image_selection_metadata_path.format(config.training_data_version)
metadata = pd.read_csv(metadata_path)

# sample of 100 images per class
sample_size = 100
metadata = metadata.groupby(['surface_clean', 'smoothness']).sample(sample_size, random_state=1)

classified_by_everyone = 10
third_size = int((sample_size-classified_by_everyone) / 3)

df_sorted = pd.DataFrame()
# Iterate through each third for each surface + 10 images per class for everyone at the beginning
for i in range(4):
    for surface in metadata.surface_clean.unique():
        for smoothness in metadata.smoothness.unique():
            # Select the corresponding third for the current surface
            if i == 0:
                current_third = metadata[(metadata['surface_clean'] == surface )& 
                                        (metadata['smoothness'] == smoothness)][0:classified_by_everyone]
            else:
                current_third = metadata[(metadata['surface_clean'] == surface )& 
                                        (metadata['smoothness'] == smoothness)][classified_by_everyone + ((i-1) * third_size): classified_by_everyone + (i * third_size)]



            # Append the current third to the sorted DataFrame
            df_sorted = pd.concat([df_sorted, current_third])

df_sorted.to_csv(config.train_image_sample_metadata_path.format(config.training_data_version), index=False)


import utils
folder = config.train_image_sample_path.format(config.training_data_version)
for image_id in df_sorted.id:
    # download sample
    utils.download_image(image_id, folder)