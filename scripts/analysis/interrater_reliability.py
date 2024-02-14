import os

import numpy as np
import pandas as pd
import json

from sklearn.metrics import cohen_kappa_score
import krippendorff as kd

path = os.path.join("/", "Users", "alexandra", "Nextcloud-HTW", "SHARED", "SurfaceAI", "data", "mapillary_images", "training", "V4", "metadata", "interrater_reliability")
files = [
    "annotation_edith.json",
    "annotation_esther.json",
    "annotation_alex.json",
]

nostreet_values = ["(mainly) no street visible", "surface / smoothness not visible"]
unsure_revise_value = "unsure - please revise"

df = pd.DataFrame()
for file in files:
    with open(os.path.join(path, file)) as f:
        d = json.load(f)
        annotations = pd.DataFrame([entry['annotations'][0] for entry in d])
        df_annotator = pd.DataFrame()
        df_annotator["annotator"] = annotations.completed_by
        df_annotator["surface"] = [result[0]['value']['choices'][0] for result in annotations.result]
        df_annotator["surface"] = df_annotator["surface"].replace(
        [
            "compacted",
            "gravel",
            "ground",
            "fine_gravel",
            "dirt",
            "grass",
            "earth",
            "sand",
        ],
        "unpaved",
    ) # there was an error for some of the first annotated data - unpaved was not replaced
        df_annotator["smoothness"] = [result[1]['value']['choices'][0] if (result[1]['value']['choices']) else '' for result in annotations.result]
        df_annotator["res2"] = [result[2]['value']['choices'][0] if (result[2]['value']['choices'])  else '' for result in annotations.result]
        df_annotator["res3"] = [result[3]['value']['choices'][0] if (len(result) > 3)  else '' for result in annotations.result]
        df_annotator["image_id"] = [entry['data']['image'] for entry in d]
        df_annotator["image_id"] = df_annotator.image_id.apply(
        lambda x: str.split(
            x, "https://freemove.f4.htw-berlin.de/data/local-files/?d=00_sample/"
        )[1]
    ).apply(lambda x: int(str.split(x, ".jpg")[0]))
        df = pd.concat([df, df_annotator])


    df.loc[df["smoothness"] == "very bad", "smoothness"] = "very_bad"
    df.loc[(df.res2.isin(nostreet_values) )| (df.res3.isin(nostreet_values) ), "nostreet"] = "nostreet"
    df.loc[(df.res2.isin == unsure_revise_value) | (df.res3 == unsure_revise_value), "nostreet"] = "revise"
    df.drop(columns=["res2", "res3"], inplace=True)
    df.loc[df.nostreet == 'nostreet', "surface"] = "nostreet"
    df.loc[df.nostreet == 'nostreet', "smoothness"] = "nostreet"


# compare predictions(with nostreet)
image_id_counts = df.groupby(["image_id"]).size()
image_ids = image_id_counts[image_id_counts == 3].index
grouped_surface = df[df.image_id.isin(image_ids) ].groupby(["image_id", "surface"]).size()

# same surface rating 
round(100* len(grouped_surface[grouped_surface == 3]) / len(grouped_surface), 2)
# 64%
# TODO: Cohens kappa for interrater reliability

# same smoothness rating
grouped_smoothness = df[df.image_id.isin(image_ids) ].groupby(["image_id", "smoothness"]).size()
round(100* len(grouped_smoothness[grouped_smoothness == 3]) / len(grouped_smoothness), 2)
# 30%


# compare predictions (without nostreet)
image_id_counts = df[df.surface != "nostreet"].groupby(["image_id"]).size()
image_ids = image_id_counts[image_id_counts == 3].index
grouped_surface = df[df.image_id.isin(image_ids) ].groupby(["image_id", "surface"]).size()

# same surface rating (with nostreet)
round(100* len(grouped_surface[grouped_surface == 3]) / len(grouped_surface), 2)
# 70%

# where is it different?
#grouped_surface[grouped_surface != 3]

# same smoothness rating
grouped_smoothness = df[df.image_id.isin(image_ids) ].groupby(["image_id", "smoothness"]).size()
round(100* len(grouped_smoothness[grouped_smoothness == 3]) / len(grouped_smoothness), 2)
# 31%


# Compute Cohen's Kappa
image_id_counts = df[df.surface != "nostreet"].groupby(["image_id"]).size()
image_ids = image_id_counts[image_id_counts == 3].index

for i,j in [(1,3), (1,4), (3,4)]:
            rater1 = df[(df.image_id.isin(image_ids)) & (df.annotator == i)].sort_values(by=["image_id"])
            rater2 = df[(df.image_id.isin(image_ids) )& (df.annotator == j)].sort_values(by=["image_id"])
            kappa = cohen_kappa_score(rater1.surface.tolist(), rater2.surface.tolist())
            print(f"Kappa for surface and annotator {i} and {j}: {round(kappa, 2)}")
            kappa = cohen_kappa_score(rater1.smoothness.tolist(), rater2.smoothness.tolist())
            print(f"Kappa for smoothness and annotator {i} and {j}: {round(kappa, 2)}")


rater1 = df[(df.image_id.isin(image_ids)) & (df.annotator == 1)].sort_values(by=["image_id"])
rater2 = df[(df.image_id.isin(image_ids) )& (df.annotator == 3)].sort_values(by=["image_id"])
rater3 = df[(df.image_id.isin(image_ids) )& (df.annotator == 4)].sort_values(by=["image_id"])
krippendorfs_alpha_surf = kd.alpha(np.array([
                rater1.surface.tolist(), 
                rater2.surface.tolist(),
                rater3.surface.tolist()]), level_of_measurement='nominal')
krippendorfs_alpha_smooth = kd.alpha(np.array([
                rater1.smoothness.tolist(), 
                rater2.smoothness.tolist(),
                rater3.smoothness.tolist()]), level_of_measurement='nominal')

print(f"Krippendorfs alpha for surface: {round(krippendorfs_alpha_surf, 2)}")
print(f"Krippendorfs alpha for surface: {round(krippendorfs_alpha_smooth, 2)}")
