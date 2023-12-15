import pandas as pd
import json

# setting path
import sys
sys.path.append('./')
import config
import constants as const

def training_entity(row, img_folder):
         return {
            "data": {"image": f"{img_folder}/{row['id']}.jpg"},
            "predictions": [
                {
                    "result": [
                        {
                            "from_name": "surface",
                            "to_name": "image",
                            "type": "choices",
                            "value": {
                            "choices": [
                                row['surface']
                                ]
                                }
                        },
                        {
                            "from_name": "smoothness",
                            "to_name": "image",
                            "type": "choices",
                            "value": {
                            "choices": 
                                [row['smoothness']
                                ]
                                }
                        },
                        {
                            "from_name": "nostreet",
                            "to_name": "image",
                            "type": "choices",
                            "value": {
                            "choices": 
                                [
                                ]
                                }
                        }
                    ]
                }
            ]
            }

def test_entity(row, img_folder):
    entity= {"data": {"image": f"{img_folder}/{row['id']}.jpg"}}
    
    # only add predictions if there is a surface, otherwise error from labelstudio
    if isinstance(row['surface'], str):
        entity["predictions"] = [
                        {
                            "result": [
                                {
                                    "from_name": "surface",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": [
                                        row['surface']
                                        ]
                                        }
                                },
                                {
                                    "from_name": "smoothness",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": 
                                        [row['smoothness']
                                        ]
                                        }
                                },
                                {
                                    "from_name": "surface_cycleway",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": [
                                        ]
                                        }
                                },
                                {
                                    "from_name": "smoothness_cycleway",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": 
                                        [
                                        ]
                                        }
                                },
                                {
                                    "from_name": "surface_pedestrian",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": [
                                        
                                        ]
                                        }
                                },
                                {
                                    "from_name": "smoothness_pedestrian",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": 
                                        [
                                        ]
                                        }
                                },
                                
                                {
                                    "from_name": "nostreet",
                                    "to_name": "image",
                                    "type": "choices",
                                    "value": {
                                    "choices": 
                                        [
                                        ]
                                        }
                                }
                            ]
                        }
                    ]
    return entity

def create_labelstudio_input_file(is_testdata, metadata_path, img_url, output_path):

    df = pd.read_csv(metadata_path)
    df["surface"] = df.surface.str.strip()
    df["smoothness"] = df.smoothness.str.strip()

    # Convert each row to JSON object and collect them in a list
    json_data = []
    for _, row in df.iterrows():
        if is_testdata:
            entity = test_entity(row, img_url)
        else:
            entity = training_entity(row, img_url)
        json_data.append(entity)

    result_json_str = json.dumps(json_data, indent=2)


    # Write JSON string to a file
    with open(output_path, 'w') as file:
        file.write(result_json_str)


if __name__ == "__main__":
    ### test data
    city = const.COLOGNE
    metadata_path = config.test_image_metadata_with_tags_path.format(city)
    img_url = config.labelstudio_absolute_path.format(f"test_data/{city}/images")
    output_path = f"data/{city}/predictions.json"
    create_labelstudio_input_file(True, metadata_path, img_url, output_path)

    ### training data
    # entire dataset
    #metadata_path = config.train_image_selection_metadata_path.format(config.training_data_version)

    # only sample
    metadata_path = config.train_image_sample_metadata_path.format(config.training_data_version)
    img_url = config.labelstudio_absolute_path.format("00_sample")
    output_path = config.labelstudio_predictions_path.format(config.training_data_version)
    create_labelstudio_input_file(False, metadata_path, img_url, output_path)
    