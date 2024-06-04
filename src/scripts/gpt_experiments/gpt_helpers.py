import os
from torchvision import transforms
from io import BytesIO
from PIL import Image 
import base64


#Takes a PIL image as input and encodes in base64 format
def encode_image(im):
    with BytesIO() as buffer:
        im.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    
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
    else:  # None, or not valid
        return img

    cropped_img = transforms.functional.crop(img, top, left, height, width)
    return cropped_img


#load, crop and encode images
def load_and_encode_image(file, data_path):
    image_id = os.path.splitext(file)[0]
    image_path = os.path.join(data_path, file)
    image = Image.open(image_path)
    image = custom_crop(image, crop_style="lower_middle_half")
    encoded_image = encode_image(image)
    return image_id, encoded_image, image


# Mapping function
def map_result(value):
    if value == 'excellent':
        return 0
    elif value == 'good':
        return 1
    elif value == 'intermediate':
        return 2
    elif value == 'bad':
        return 3
    else: 
        return 9
    







