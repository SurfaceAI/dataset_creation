import sys
sys.path.append('.')

from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from torchvision import transforms, models
from functools import partial
from sentence_transformers import SentenceTransformer, util
import torch
import os
from pathlib import Path
from PIL import Image
import pickle

import embedding_helpers


# define embedding model, dataset, embeddings saving name
config = {
    'embedding_model_name': 'clip', # 'dino', 'efficientnet_v2_s', 'clip'
    'dataset': 'V200/sorted_images',
    'crop': 'lower_middle_half',
    'name_output': 'V200_effnet_cropped_sim_embeddings.pkl',
    'gpu_kernel': 0,
}


device = torch.device(
    f"cuda:{config.get('gpu_kernel')}" if torch.cuda.is_available() else "cpu"
)

embedding_model_name = config.get('embedding_model_name')

crop = config.get('crop')

data_path = embedding_helpers.data_path
embeddings_path = embedding_helpers.embeddings_path
images_path = os.path.join(data_path, config.get('dataset'))

embeddings_file = os.path.join(embeddings_path, config.get('name_output'))

if not os.path.exists(embeddings_path):
    os.mkdir(embeddings_path)

class dino_embed():
    def __init__(self) -> None:

        self.model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')

    @staticmethod
    def transform(image):
        transform = transforms.Compose([ 
            transforms.Lambda(partial(embedding_helpers.custom_crop, crop_style=crop)),
            transforms.Resize((224, 224)), 
            transforms.ToTensor(), 
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)), 
        ]) 
        return transform(image)

    def embed(self, image):
        img = self.transform(image).unsqueeze(0).to(device)

        # Move model to GPU
        self.model.to(device)
        self.model.eval()

        # run inference
        with torch.no_grad():
            embedding = self.model(img)

        return embedding.squeeze(0)
    
class clip_embed():
    def __init__(self) -> None:

        self.model = SentenceTransformer('clip-ViT-B-32')

    def embed(self, image):
        # run inference
        image = preprocessing.custom_crop(image, crop_style=crop)
        embedding = self.model.encode(image, convert_to_tensor=True)

        return embedding
    
class pretrained_model_embed():
    def __init__(self) -> None:
        self.model = models.efficientnet_v2_s(weights='IMAGENET1K_V1')
        self.feature_layer = self.model.features
        self.avgpool = self.model.avgpool
        

    @staticmethod
    def transform(image):
        transform = transforms.Compose([ 
            transforms.Lambda(partial(embedding_helpers.custom_crop, crop_style=crop)),
            transforms.Resize((384, 384)), 
            transforms.ToTensor(), 
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)), 
        ]) 
        return transform(image)

    def embed(self, image):
        img = self.transform(image).unsqueeze(0).to(device)

        # Move model to GPU
        self.model.to(device)
        self.model.eval()

        # run inference
        with torch.no_grad() and embedding_helpers.ActivationHook(self.feature_layer) as activation_hook:
            _ = self.model(img)
            embedding = activation_hook.activation.squeeze(0)
        
        embedding = torch.flatten(self.avgpool(embedding))

        return embedding

images = []
for root, _, fnames in sorted(os.walk(images_path, followlinks=True)):
    for fname in sorted(fnames):
        path = os.path.join(root, fname)
        if fname.endswith((".jpg", ".jpeg", ".png")):
            images.append(path)

if embedding_model_name == 'dino':
    embedding_model = dino_embed()
elif embedding_model_name == 'clip':
    embedding_model = clip_embed()
elif embedding_model_name == 'efficientnet_v2_s':
    embedding_model = pretrained_model_embed()
else:
    print('No valid embedding model.')

embeddings = []
for image_path in images:
    image = Image.open(image_path)
    embedding = embedding_model.embed(image)
    embeddings.append(embedding)

result = torch.stack(embeddings).cpu()

with open(embeddings_file, "wb") as f_out:
    pickle.dump({'images': images, 'embeddings': result}, f_out, protocol=pickle.HIGHEST_PROTOCOL)

print('Done.')