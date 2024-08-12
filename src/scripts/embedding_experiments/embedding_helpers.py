import os
from torchvision import transforms
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

data_path = str(ROOT_DIR / "data")
embeddings_path = str(ROOT_DIR / "embeddings")
models_path = str(ROOT_DIR / "trained_models")
results_path = str(ROOT_DIR/ "results")
gpt_results_path = str(ROOT_DIR/ "results")
# experiments_path = str(ROOT_DIR/ "annotation_experiments")
# gpt_results_path = str(ROOT_DIR/ "annotation_experiments" / "gpt_results")


class ActivationHook:
    def __init__(self, module):
        self.module = module
        self.hook = None
        self.activation = None

    def __enter__(self):
        self.hook = self.module.register_forward_hook(self.hook_func)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def hook_func(self, module, input, output):
        self.activation = output.detach()

    def close(self):
        if self.hook is not None:
            self.hook.remove()

#cropping function
def custom_crop(img, crop_style=None):
    im_width, im_height = img.size
    if crop_style == "lower_middle_third":
        top = im_height / 3 * 2
        left = im_width / 3
        height = im_height - top
        width = im_width / 3
    elif crop_style == "lower_middle_half":
        top = im_height / 2
        left = im_width / 4
        height = im_height / 2
        width = im_width / 2
    elif crop_style == "lower_half":
        top = im_height / 2
        left = 0
        height = im_height / 2
        width = im_width
    else:  # None, or not valid
        return img

    cropped_img = transforms.functional.crop(img, top, left, height, width)
    return cropped_img

def extract_type_and_quality_and_id_from_img_path(img_path):
    #"no_street", "not_recognizable","revise"
    valid_types = ["asphalt", "concrete", "paving_stones", "sett", "unpaved"]
    path_split = img_path.split('/') #todo. change back to ('\\')'/'
    extracted_type = path_split[-3]
    if extracted_type in valid_types:
        extracted_quality = path_split[-2]
    else:
        extracted_type = path_split[-2]
        extracted_quality = None
    extracted_id = os.path.splitext(path_split[-1])[0]
    return extracted_type, extracted_quality, extracted_id


