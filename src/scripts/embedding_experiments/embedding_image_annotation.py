import sys
sys.path.append('.')

import os
import pickle 

import pandas as pd
import numpy as np 
import random

from sentence_transformers import util
import torch 

import matplotlib.pyplot as plt

import embedding_helpers


# config
query_dataset = 'V12' # fixed
embeddings_model_list = [
    'clip',
    'dino',
    'effnet',
    ]
embeddings_postfix = 'cropped_sim_embeddings.pkl'
gpu_kernel = 0

experiments_list = [
    {'name': 'experiment_0',
     'corpus_dataset': 'V12',
     'is_threshold_given': False,
     'is_quality_preselected': False},
    {'name': 'experiment_1',
     'corpus_dataset': 'V101',
     'is_threshold_given': True,
     'is_quality_preselected': True},
    {'name': 'experiment_2',
     'corpus_dataset': 'V200',
     'is_threshold_given': True,
     'is_quality_preselected': False,
     },
]

conditions_list = [
    {'surface_type': 'asphalt', 'surface_quality': 'bad'},
    {'surface_type': 'paving_stones', 'surface_quality': 'intermediate'},
    {'surface_type': 'paving_stones', 'surface_quality': 'bad'},
]


device = torch.device(
    f"cuda:{gpu_kernel}" if torch.cuda.is_available() else "cpu"
)
print(device)

embeddings_path = embedding_helpers.embeddings_path
gpt_results_path = embedding_helpers.gpt_results_path
results_path = embedding_helpers.results_path

def search_dataset(query_embeddings, query_images, corpus_embeddings, corpus_images, score_threshold=None):
    results = pd.DataFrame()
    for query_embedding, idx in zip(query_embeddings, query_images.index):
        non_duplicates = ~(corpus_images['image_id']==query_images['image_id'][idx])
        k = len(corpus_embeddings[non_duplicates])
        hits = util.semantic_search(query_embedding, corpus_embeddings[non_duplicates], top_k=k+1)[0]
        if score_threshold is not None:
            hits = [hit for hit in hits if hit['score'] > score_threshold]

        files_scores = {corpus_images[non_duplicates].reset_index(drop=True)['image_id'][hit['corpus_id']]:hit['score'] for hit in hits}
        files_scores = pd.DataFrame(list(files_scores.items()), columns=['image_id', 'score'])

        results = pd.concat([results, files_scores], ignore_index=True)

    unique_results = results.loc[results.groupby('image_id')['score'].idxmax()].reset_index(drop=True)
    df = unique_results.join(corpus_images[['image_id', 'type', 'quality']].set_index('image_id'), how="left", on='image_id').sort_values(by='score', ascending=False)
    return df

def calculate_metrics(search_results, corpus_images, surface_quality, score_threshold):
    search_results_threshold = search_results[search_results['score'] > score_threshold]
    condition = (corpus_images["quality"] == surface_quality)

    all_paths = set(corpus_images['image_id'].values)
    predicted_positives = set(search_results_threshold['image_id'])
    actual_positives = set(corpus_images[condition]['image_id'].values)
    predicted_negatives = all_paths.difference(predicted_positives)
    actual_negatives = all_paths.difference(actual_positives)
    
    TP_count = len(actual_positives.intersection(predicted_positives))
    FP_count = len(predicted_positives.difference(actual_positives))
    TN_count = len(actual_negatives.intersection(predicted_negatives))
    FN_count = len(actual_positives.difference(predicted_positives)) # = len(predicted_negatives.difference(actual_negatives))
    
    return TP_count, FP_count, TN_count, FN_count
    

def find_optimal_ROC_threshold(unique_search_results, corpus_images, surface_quality):

    thresholds = np.linspace(0, 1, 40)
    tprs = []
    fprs = []
    tps = []
    fps = []
    tns = []
    fns = []
    youdens_j = []
    f1 = []
    
    for threshold in thresholds:
        TP, FP, TN, FN = calculate_metrics(unique_search_results, corpus_images, surface_quality, threshold)
        TPR = TP / (TP + FN) 
        FPR = FP / (FP + TN)
        F1 = 0.0 if TP == 0 else (2 * TP / (2 * TP + FP + FN))
        tprs.append(TPR)
        fprs.append(FPR)
        tps.append(TP)
        fps.append(FP)
        tns.append(TN)
        fns.append(FN)
        youdens_j.append(TPR - FPR)
        f1.append(F1)
    
    optimal_idx = np.argwhere(youdens_j == np.amax(youdens_j)) # optimal_idx = np.argmax(youdens_j)
    optimal_idx = optimal_idx.flatten().tolist()[0] # -1 alternative
    optimal_threshold = thresholds[optimal_idx]
    maxF1 = np.max(f1)
    
    TP, FP, TN, FN = tps[optimal_idx], fps[optimal_idx], tns[optimal_idx], fns[optimal_idx]

    return optimal_threshold, TP, FP, TN, FN, maxF1, tprs, fprs

def plot_roc_curve(tprs_list, fprs_list, surface_type, surface_quality, save_file):

    # plot diagonal
    plt.figure()
    plt.plot([0, 1], [0, 1], color='red', linestyle='--')
    
    # plot ROC curve
    for tprs, fprs in zip(tprs_list, fprs_list):
        plt.plot(fprs, tprs, marker='o')

    plt.title(f'ROC-curve for {surface_type} - {surface_quality}')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    # plt.legend()

    # save and close plot
    plt.savefig(save_file)
    plt.close

for experiment in experiments_list:
    experiment_name =experiment['name'] 
    corpus_dataset = experiment['corpus_dataset']
    is_threshold_given = experiment['is_threshold_given']
    is_quality_preselected = experiment['is_quality_preselected']
    for embeddings_model in embeddings_model_list:
        query_embeddings_file = f'{query_dataset}_{embeddings_model}_{embeddings_postfix}'
        corpus_embeddings_file = f'{corpus_dataset}_{embeddings_model}_{embeddings_postfix}'

        results_list = []
        threshold_experiment_name = f'_ROC_threshold_{embeddings_model}.csv'

        for condition in conditions_list:
            surface_type, surface_quality = condition['surface_type'], condition['surface_quality']

            print(f'\nModel: {embeddings_model}, Surface type: {surface_type}, Surface quality: {surface_quality}')

            experiment_file = f'{corpus_dataset}_{embeddings_model}_{surface_type}_{surface_quality}.csv'
            
            # QUERY
            # Load images & embeddings from disc
            with open(os.path.join(embeddings_path, query_embeddings_file), "rb") as f_in:
                query_data = pickle.load(f_in)
                query_images = query_data['images']
                query_embeddings = query_data['embeddings']

            df = pd.DataFrame(query_images, columns=["path"])
            df[['type', 'quality', 'image_id']] = df.apply(lambda x: embedding_helpers.extract_type_and_quality_and_id_from_img_path(x["path"]), axis=1, result_type='expand')

            # surface_type embeddings
            query_condition = (df['type'] == surface_type) & (df['quality'] == surface_quality)
            
            query_images = df[query_condition].reset_index(drop=True)
            query_embeddings = query_embeddings[query_condition].to(device)

            is_batch_limit_reached = True
            batch = 1

            while True:
                # CORPUS
                # Load images & embeddings from disc
                with open(os.path.join(embeddings_path, corpus_embeddings_file), "rb") as f_in:
                    corpus_data = pickle.load(f_in)
                    corpus_images = corpus_data['images']
                    corpus_embeddings = corpus_data['embeddings']

                df = pd.DataFrame(corpus_images, columns=["path"])
                df[['type', 'quality', 'image_id']] = df.apply(lambda x: embedding_helpers.extract_type_and_quality_and_id_from_img_path(x["path"]), axis=1, result_type='expand')

                # surface_type embeddings
                if is_quality_preselected:
                    corpus_condition = (df['type'] == surface_type) & (df['quality'] == surface_quality)
                else:
                    corpus_condition = (df['type'] == surface_type)
                corpus_images = df[corpus_condition].reset_index(drop=True)
                corpus_embeddings = corpus_embeddings[corpus_condition].to(device)

                # only images used in GPT experiments 1 & 2
                if experiment_name == 'experiment_1':
                    gpt_images_list = pd.read_csv(os.path.join(gpt_results_path, f'{experiment_name}_{corpus_dataset}_{surface_type}_{surface_quality}.csv'))
                    corpus_condition = corpus_images['image_id'].isin(gpt_images_list['image_id'].astype(str))
                    corpus_images = corpus_images[corpus_condition].reset_index(drop=True)
                    corpus_embeddings = corpus_embeddings[corpus_condition]
                elif experiment_name == 'experiment_2':
                    is_batch_limit_reached = False
                    try:
                        gpt_images_list = pd.read_csv(os.path.join(gpt_results_path, f'{experiment_name}_{corpus_dataset}_{surface_type}_batch_{batch}.csv'))
                        experiment_file = f'{corpus_dataset}_{embeddings_model}_{surface_type}_{surface_quality}_batch_{batch}.csv'
                        print(f'Batch {batch}')
                        batch += 1
                    except:
                        break
                    corpus_condition = corpus_images['image_id'].isin(gpt_images_list['image_id'].astype(str))
                    corpus_images = corpus_images[corpus_condition].reset_index(drop=True)
                    corpus_embeddings = corpus_embeddings[corpus_condition]

                if is_threshold_given:
                    df = pd.read_csv(os.path.join(results_path, threshold_experiment_name))
                    # optimal_threshold = df['optimal_threshold'][0]
                    optimal_threshold = df[(df['surface_type'] == surface_type) & (df['surface_quality'] == surface_quality)]['optimal_threshold'].mean()
                    print(f'optimal threshold mean: {optimal_threshold}')
                    
                    search_results = search_dataset(query_embeddings, query_images, corpus_embeddings, corpus_images)
                    search_results['searched_quality_predicted'] = (search_results['score'] > optimal_threshold).astype(str)
                    search_results.to_csv(os.path.join(results_path, experiment_file))      
                
                else:
                    # QUERY
                    tprs_list = []
                    fprs_list = []
                    # choose random query from corpus
                    for seed in [42, 1000, 3]:
                        random.seed(seed)
                        indices = query_images.index
                        query_indices = random.sample(list(indices), min(50, round(len(indices)*2/3)))
                        # query_indices = random.sample(list(indices), min(50, len(indices)))
                        query_images =query_images.iloc[query_indices].reset_index(drop=True)
                        query_embeddings = query_embeddings[query_indices].to(device)

                        search_results = search_dataset(query_embeddings, query_images, corpus_embeddings, corpus_images)

                        optimal_threshold, TP, FP, TN, FN, maxF1, tprs, fprs = find_optimal_ROC_threshold(search_results, corpus_images, surface_quality)
                        tprs_list.append(tprs)
                        fprs_list.append(fprs)

                        results_list.append({'surface_type': surface_type,
                                            'surface_quality': surface_quality,
                                            'seed': seed,
                                            'optimal_threshold': optimal_threshold,
                                            'TP': TP,
                                            'FP': FP,
                                            'TN': TN,
                                            'FN': FN,
                                            'random_Precision': round((TP+FN) / (FP+TN), 3),
                                            'Precision': round(0.0 if TP == 0 else (TP / (TP + FP)), 3),
                                            'Recall': round(0.0 if TP == 0 else (TP / (TP + FN)), 3),
                                            'F1': round(0.0 if TP == 0 else (2 * TP / (2 * TP + FP + FN)), 3),
                                            'max_F1': round(maxF1, 3),
                                            })

                        if not os.path.exists(results_path):
                            os.makedirs(results_path)
                            
                        print(f'optimal_threshold: {optimal_threshold:.3f}, TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}')
                        print(f'Precision: {0.0 if TP == 0 else (TP / (TP + FP)):.3f}, Recall: {0.0 if TP == 0 else (TP / (TP + FN)):.3f}')
                        print(f'F1: {0.0 if TP == 0 else (2 * TP / (2 * TP + FP + FN)):.3f}, maxF1: {maxF1:.3f}')

                        search_results['searched_quality_predicted'] = (search_results['score'] > optimal_threshold).astype(str)
                        search_results.to_csv(os.path.join(results_path, f'seed{seed}_{experiment_file}'))

                    plot_name = os.path.join(results_path, f'ROC_{embeddings_model}_{surface_type}_{surface_quality}.png')
                    plot_roc_curve(tprs_list, fprs_list, surface_type, surface_quality, plot_name)

                    threshold_results = pd.DataFrame(results_list)
                    threshold_results.to_csv(os.path.join(results_path, threshold_experiment_name)) 

                if is_batch_limit_reached:
                    break
