import sys
sys.path.append('.')
import os
from openai import OpenAI
import pandas as pd
import pandas as pd
import gpt4v_prompting_definitions
from pathlib import Path
from gpt_helpers import *
from OpenAI_API import API_KEY
import time

#Config
random_state = 2
dataset = 'V101'
surface_type = 'asphalt'
quality_type = 'bad'  
experiment = '1'
subsample = None
batch_id = None
client = OpenAI(api_key=API_KEY) 
definition = gpt4v_prompting_definitions
instructions = gpt4v_prompting_definitions.INSTRUCTIONS_EXCLUDE_NO_FOCUS
gpt_model = 'gpt-4o'

#path definition
if quality_type is not None:
    if batch_id is not None:
        save_name = f'experiment_{experiment}_{dataset}_{surface_type}_{quality_type}_batch_{batch_id}.csv'
    else:
        save_name = f'experiment_{experiment}_{dataset}_{surface_type}_{quality_type}.csv'
else:
    if batch_id is not None:
        save_name = f'experiment_{experiment}_{dataset}_{surface_type}_batch_{batch_id}.csv'
    else:
        save_name = f'experiment_{experiment}_{dataset}_{surface_type}.csv'

ROOT_DIR = Path(__file__).parent
data_path = str(ROOT_DIR / "data" / dataset / surface_type)
sample_data_path = str(ROOT_DIR / "one_shot_images" / f"{surface_type}")
results_path = str(ROOT_DIR / 'results')

#surface type definitions
surface_type_definitions = {
    "asphalt": definition.DEFINITION_ASPHALT,
    "concrete": definition.DEFINITION_CONCRETE,
    "paving_stones": definition.DEFINITION_PAVING_STONES,
    "sett": definition.DEFINITION_SETT,
    "unpaved": definition.DEFINITION_UNPAVED,
}



#load sample images for one-shot prediction
dir = os.path.join(sample_data_path, 'excellent')
files = os.listdir(dir)
_, excellent_encoded_image, excellent_image = load_and_encode_image(files[0], dir)

dir = os.path.join(sample_data_path, 'good')
files = os.listdir(dir)
_, good_encoded_image, good_image = load_and_encode_image(files[0], dir)

dir = os.path.join(sample_data_path, 'intermediate')
files = os.listdir(dir)
_, intermediate_encoded_image, intermediate_image = load_and_encode_image(files[0], dir)

dir = os.path.join(sample_data_path, 'bad')
files = os.listdir(dir)
_, bad_encoded_image, bad_image = load_and_encode_image(files[0], dir)


#function to execute one API call
def get_single_prediction(image, definition, instructions, gpt_model, random_state):  
    
    messages = [
    {
        "role": "system", 
        "content": [
            {
                "type": "text",
                "text": "You are a data annotation expert trained to classify the quality level of road surfaces in images."
                },
        ]
    },    
    {
        "role": "user", 
        "content": [
                {
                "type": "text",
                "text": f""" 
                        You need to determine the quality level of the road surface depicted in the image, following this defined scale: {definition}.
                        Please adhere to the following instructions: {instructions}. 
                        How would you rate this image using one of the four options of the defined scale: 
                        1) excellent
                        2) good
                        3) intermediate
                        4) bad
                        
                        Provide your rating in one word disregarding the bullet point numbers and brackets as a string using the four levels of the scale provided.  
                        Make sure you have the same number of image urls as input as you have output values.

                        Do not provide any additional explanations for your rating; focus solely on the road surface quality."""
                },
                
                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{excellent_encoded_image}"
                            },   
                },
                    
                {
                "type": "text",
                "text": "This was an example for 'excellent'"
                },
                
                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{good_encoded_image}"
                            },   
                },
                    
                {
                "type": "text",
                "text": "This was an example for 'good'"
                },
                
                
                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{intermediate_encoded_image}"
                            },   
                },
                    
                {
                "type": "text",
                "text": "This was an example for 'intermediate'"
                },
                
                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{bad_encoded_image}"
                            },   
                },
                    
                {
                "type": "text",
                "text": "This was an example for 'bad'"
                },
                
                    
                {
                "type": "text",
                "text": "Please decide now in one word which category the following picture belongs to as instructed in the beginning of the prompt. Then compare this image to the previous ones and decide whether this category is correct."
                },
                
                {
                "type": "image_url",
                "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                            }, 
                },
                
                    ],                  
    },                  
    
    ]
    
    
 
    completion = client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        max_tokens=200,
        n=1,
        temperature=0,
        seed=random_state,
    )

    response_text = completion.choices[0].message.content
    return response_text
    
   

#function to execute multiple api calls and save predictions
def get_multiple_predictions(df, definition, instructions, gpt_model, surface_type, random_state):
    #new data frame for saving predictions
    single_predictions = pd.DataFrame(columns = ['image_id',
                                                 'preselection_type',
                                                 'preselection_quality',
                                                 'prediction', 
                                                ])
 
    for index, row in df.iterrows():
        
        try:
    
            response = get_single_prediction(df['encoded_image'][index], definition, instructions, gpt_model, random_state) 
            
            
            pred_multi = pd.DataFrame({'image_id': [row['image_id']],
                                    'preselection_type': [surface_type],
                                    'preselection_quality': [quality_type],
                                    'prediction': [response],
                                    })
            
            single_predictions = pd.concat([single_predictions, pred_multi], ignore_index=True)
            single_predictions['image_id'] = single_predictions['image_id'].astype('int64')
            
            single_predictions.to_csv(os.path.join(results_path, save_name), index=False)
            
            print(len(single_predictions['prediction']), ' samples saved')
            
        except Exception as e:
            print(f"Error processing image {row['image_id']}: {e}")
            continue
    
    return single_predictions


#load complete dataset
image_ids = []
encoded_images = []
true_labels = []

if quality_type is not None:
    dir = os.path.join(data_path, quality_type)
else: 
    dir = data_path
files = os.listdir(dir)

for file in files:
    image_id, encoded_image, _ = load_and_encode_image(file, dir) 
    image_ids.append(image_id)
    encoded_images.append(encoded_image)
    true_labels.append(quality_type)

df = pd.DataFrame({"image_id": image_ids, "encoded_image": encoded_images, "true_label": true_labels})
df['image_id'] = df['image_id'].astype('int64')

#take subsample if necessary
if subsample is not None:
    for i in range(1, batch_id + 1):
        df_subsample = df.sample(n=subsample, random_state=random_state).reset_index(drop=True)
        if i == batch_id:
            df = df_subsample
        else:
            df = df[~df.image_id.isin(df_subsample.image_id)]
    
    
#prediction
start_time = time.time()
single_predictions = get_multiple_predictions(df, surface_type_definitions.get(surface_type), 
                                              instructions=instructions, 
                                              gpt_model=gpt_model, 
                                              surface_type=surface_type, 
                                              random_state=random_state,
                                              )

end_time = time.time()

#calculate execution time
execution_time = end_time - start_time
print(f"Execution time: {execution_time} seconds")
