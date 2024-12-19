import os
from torchvision import transforms, models
import torch
from torch import nn, Tensor
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent

data_path = str(ROOT_DIR / "data")
embeddings_path = str(ROOT_DIR / "embeddings")
models_path = str(ROOT_DIR / "trained_models")
results_path = str(ROOT_DIR / "embeddings" / "results")
gpt_results_path = str(ROOT_DIR / "gpt" / "results")
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

class CustomEfficientNetV2SLinear(nn.Module):
    def __init__(self, num_classes):
        super(CustomEfficientNetV2SLinear, self).__init__()

        model = models.efficientnet_v2_s(weights='IMAGENET1K_V1')
        # adapt output layer
        in_features = model.classifier[-1].in_features
        fc = nn.Linear(in_features, num_classes, bias=True)
        model.classifier[-1] = fc
        
        self.features = model.features
        self.avgpool = model.avgpool
        self.classifier = model.classifier
        if num_classes == 1:
            self.criterion = nn.MSELoss
        else:
            self.criterion = nn.CrossEntropyLoss
        
    @ staticmethod
    def get_class_probabilies(x):
        return nn.functional.softmax(x, dim=1)

    def forward(self, x: Tensor) -> Tensor:
        x = self.features(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)

        x = self.classifier(x)

        return x
    
    def get_optimizer_layers(self):
        return self.classifier

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

def load_model(model_path, device):
    model_state = torch.load(model_path, map_location=device)

    if model_state['config']['model'] == "efficientNetV2SLinear":
        model_cls = CustomEfficientNetV2SLinear
    else:
        print("No valid model.")
    is_regression = model_state['config']["is_regression"]
    # is_regression = False
    valid_dataset = model_state['dataset']

    if is_regression:
        class_to_idx = get_attribute(valid_dataset, "class_to_idx")
        classes = {str(i): cls for cls, i in class_to_idx.items()}
        num_classes = 1
    else:
        classes = get_attribute(valid_dataset, "classes")
        num_classes = len(classes)
    model = model_cls(num_classes)
    model.load_state_dict(model_state['model_state_dict'])

    return model, classes, is_regression, valid_dataset

def get_attribute(obj, attribute_name):
    # check for dict
    if isinstance(obj, dict):
        return obj.get(attribute_name)
    # check for class instance
    elif hasattr(obj, attribute_name):
        return getattr(obj, attribute_name)
    else:
        raise TypeError("Object is not a dictionary or a class instance.")

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


