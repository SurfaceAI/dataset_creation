# create cropping frame

import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import os


def save_image_with_lines(image_path, output_path):
    # Open the image file
    img = Image.open(image_path)
    img_arr = np.array(img)
    
    fig, ax = plt.subplots()
    ax.imshow(img_arr)

    # Get the dimensions of the image
    height, width, _ = img_arr.shape

    # Calculate the positions of the lines
    middle_horizontal = height // 2
    one_third_vertical = width // 4
    two_thirds_vertical = 3 * width // 4


    # Draw a horizontal line in the middle of the image
    ax.axhline(y=middle_horizontal, color='red', linewidth=2)

    # Draw two vertical lines dividing the image into thirds
    ax.axvline(x=one_third_vertical, color='red', linewidth=2)
    ax.axvline(x=two_thirds_vertical, color='red', linewidth=2)

    # Remove axis
    ax.axis('off')

    # Save the figure to a file
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=300)
    plt.close()


def process_folder(folder_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # List all files in the given folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, filename)
            save_image_with_lines(image_path, output_path)
            print(f'Processed {filename}')



if __name__ == '__main__':
    img_folder = '/Users/alexandra/Nextcloud-HTW/SHARED/SurfaceAI/data/mapillary_images/training/V11/re-classify/paving_stones'
    process_folder(os.path.join(img_folder, "misclassified"), 
                    os.path.join(img_folder, "misclassified_crop"))
