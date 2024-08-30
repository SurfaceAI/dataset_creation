import sys
sys.path.append('.')

from torchvision import transforms
from functools import partial
from sentence_transformers import SentenceTransformer
import torch
import os
from PIL import Image
import pickle
from tqdm import tqdm

import embedding_helpers

class dino_embed():
    def __init__(self, crop, device) -> None:

        self.model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14')
        self.crop = crop
        self.device = device

    def transform(self, image):
        transform = transforms.Compose([ 
            transforms.Lambda(partial(embedding_helpers.custom_crop, crop_style=self.crop)),
            transforms.Resize((224, 224)), 
            transforms.ToTensor(), 
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)), 
        ]) 
        return transform(image)

    def embed(self, image):
        img = self.transform(image).unsqueeze(0).to(self.device)

        # Move model to GPU
        self.model.to(self.device)
        self.model.eval()

        # run inference
        with torch.no_grad():
            embedding = self.model(img)

        return embedding.squeeze(0)
    
class clip_embed():
    def __init__(self, crop) -> None:

        self.model = SentenceTransformer('clip-ViT-B-32')
        self.crop = crop

    def embed(self, image):
        # run inference
        image = embedding_helpers.custom_crop(image, crop_style=self.crop)
        embedding = self.model.encode(image, convert_to_tensor=True)

        return embedding
    
class trained_model_embed():
    def __init__(self, model, crop, device) -> None:

        self.device = device
        self.crop = crop
        self.model, _, _, _ = embedding_helpers.load_model(model, self.device)
        self.feature_layer = self.model.features
        self.avgpool = self.model.avgpool
        

    def transform(self, image):
        transform = transforms.Compose([ 
            transforms.Lambda(partial(embedding_helpers.custom_crop, crop_style=self.crop)),
            transforms.Resize((384, 384)), 
            transforms.ToTensor(), 
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)), 
        ]) 
        return transform(image)

    def embed(self, image):
        img = self.transform(image).unsqueeze(0).to(self.device)
        

        # Move model to GPU
        self.model.to(self.device)
        self.model.eval()

        # run inference
        with torch.no_grad() and embedding_helpers.ActivationHook(self.feature_layer) as activation_hook:
            _ = self.model(img)
            embedding = activation_hook.activation.squeeze(0)
        
        embedding = torch.flatten(self.avgpool(embedding))

        return embedding
    
if __name__ == "__main__":
    # define embedding model, dataset, embeddings saving name
    config = {
        'embedding_model_name': 'clip', # 'clip', 'dino', 'effnet'
        # TODO: train a model and assign it to 'trained_model' to use the embedding model name 'effnet'
        'trained_model': '', # trained model file for effnet only
        'dataset': 'V12/annotated', # 'V12/annotated', 'V101/sorted_images' 'V200/sorted_images',
        'crop': 'lower_middle_half',
        'embeddings_postfix': 'cropped_sim_embeddings.pkl',
        'gpu_kernel': 0,
    }

    data_path = embedding_helpers.data_path
    embeddings_path = embedding_helpers.embeddings_path
    models_path = embedding_helpers.models_path
    images_path = os.path.join(data_path, config.get('dataset'))
    
    embedding_model_name = config.get('embedding_model_name')

    embeddings_file = os.path.join(embeddings_path, f"{config.get('dataset').split('/')[0]}_{embedding_model_name}_{config.get('embeddings_postfix')}")

    if not os.path.exists(embeddings_path):
        os.mkdir(embeddings_path)

    device = torch.device(
        f"cuda:{config.get('gpu_kernel')}" if torch.cuda.is_available() else "cpu"
    )
 
    crop = config.get('crop')

    if embedding_model_name == 'dino':
        embedding_model = dino_embed(crop=crop, device=device)
    elif embedding_model_name == 'clip':
        embedding_model = clip_embed(crop=crop)
    elif embedding_model_name == 'effnet':
        model_file = os.path.join(models_path, config.get('trained_model'))
        embedding_model = trained_model_embed(model=model_file, crop=crop, device=device)
    else:
        print('No valid embedding model.')

    images = []
    for root, _, fnames in sorted(os.walk(images_path, followlinks=True)):
        for fname in sorted(fnames):
            path = os.path.join(root, fname)
            if fname.endswith((".jpg", ".jpeg", ".png")):
                images.append(path)

    embeddings = []
    for image_path in tqdm(images, desc="embed images"):
        image = Image.open(image_path)
        embedding = embedding_model.embed(image)
        embeddings.append(embedding)

    result = torch.stack(embeddings).cpu()

    with open(embeddings_file, "wb") as f_out:
        pickle.dump({'images': images, 'embeddings': result}, f_out, protocol=pickle.HIGHEST_PROTOCOL)

    print('Done.')