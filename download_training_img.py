import pandas as pd
import os
import config
import utils
import time

metadata = pd.read_csv(config.train_image_metadata_with_tags_path)

metadata["surface"] = metadata.surface.str.strip()
metadata["smoothness"] = metadata.smoothness.str.strip()
metadata["sequence_id"] = metadata.sequence_id.str.strip()
metadata["month"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.month
metadata["hour"] = pd.to_datetime(metadata["captured_at"], unit="ms").dt.hour

metadata["surface_clean"] = metadata["surface"].replace(['compacted', 'gravel', 'ground', 'fine_gravel', 'dirt', 'grass', 'earth', 'sand'], 'unpaved')
metadata["surface_clean"] = metadata["surface_clean"].replace(['cobblestone', 'unhewn_cobblestone'], 'sett')
metadata["surface_clean"] = metadata["surface_clean"].replace('concrete:plates', 'concrete')

# drop everything not in the defined surface list
surfaces = [config.ASPHALT, config.CONCRETE, config.PAVING_STONES, config.SETT, config.UNPAVED]
smoothnesses = [config.EXCELLENT, config.GOOD, config.INTERMEDIATE, config.BAD, config.VERY_BAD]
#metadata = metadata[metadata["surface_clean"].isin(surfaces)]
#metadata = metadata[metadata["smoothness"].isin(smoothnesses)]

# drop surface specific smoothness
metadata = (metadata[
                    ((metadata["surface_clean"] == "asphalt") & (metadata["smoothness"].isin([config.EXCELLENT, config.GOOD, config.INTERMEDIATE, config.BAD])))|
                    ((metadata["surface_clean"] == "concrete") & (metadata["smoothness"].isin([config.EXCELLENT, config.GOOD, config.INTERMEDIATE, config.BAD])))|
                    ((metadata["surface_clean"] == "paving_stones") & (metadata["smoothness"].isin([config.EXCELLENT, config.GOOD, config.INTERMEDIATE, config.BAD])))|
                    ((metadata["surface_clean"] == "sett") & (metadata["smoothness"].isin([config.GOOD, config.INTERMEDIATE, config.BAD])))|
                    ((metadata["surface_clean"] == "unpaved") & (metadata["smoothness"].isin([config.INTERMEDIATE, config.BAD, config.VERY_BAD])))
                    ])

# filter date
metadata = metadata[metadata["captured_at"] >= config.time_filter_unix]
# not in winter (bc of snow)
metadata = metadata[metadata["month"].isin(range(3,11))]
# not at night (bc of bad light)
metadata = metadata[metadata["hour"].isin(range(8,18))]

# todo: remove panorama images
metadata = metadata[metadata["is_pano"] == 'f']

# sample x images per class
metadata = (metadata
            .groupby(["sequence_id"])
            .sample(config.max_img_per_sequence_training,random_state=1,replace=True)
            .drop_duplicates(subset="id")
            .groupby(["surface_clean", "smoothness"])
            .sample(config.imgs_per_class,random_state=1,replace=True)
            .drop_duplicates(subset="id"))

metadata.to_csv(config.train_image_selection_metadata_path, index=False)

start = time.time()
if not os.path.exists(config.train_image_folder):
    os.makedirs(config.train_image_folder)
    
for surface in surfaces:
    folder = os.path.join(config.train_image_folder, surface)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for smoothness in smoothnesses: 
        folder = os.path.join(config.train_image_folder, surface, smoothness)
        if not os.path.exists(folder):
            os.makedirs(folder)

        image_ids = list(metadata[(metadata["surface_clean"] == surface) & (metadata["smoothness"] == smoothness)]["id"])
        for i in range(0, len(image_ids)):
            if i % 100 == 0:
                print(f"{i} images downloaded")
            utils.download_image(image_ids[i], folder)

print(f"{round((time.time()-start )/ 60)} mins")

#metadata.groupby(['surface_clean', 'smoothness']).size()
