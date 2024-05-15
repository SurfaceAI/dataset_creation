import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.abspath(__file__)).parent.parent))


import utils as utils

if __name__ == "__main__":
    img_folder = "/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V11/re-classify/paving_stones"
    utils.crop_frame_for_img_folder(
        os.path.join(img_folder, "misclassified"),
        os.path.join(img_folder, "misclassified_crop"),
    )
