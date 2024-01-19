import os

import pandas as pd
import json

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
    df.loc[(df.res2.isin(nostreet_values) )or (df.res3.isin(nostreet_values) ), "nostreet"] = "nostreet"
    df.loc[(df.res2.isin([unsure_revise_value]) )or (df.res3.isin([unsure_revise_value])), "nostreet"] = "revise"
    df.loc[df.nostreet == 'nostreet', "surface"] = "nostreet"
    df.loc[df.nostreet == 'nostreet', "smoothness"] = "nostreet"


# compare predictions
image_id_counts = df.groupby(["image_id"]).size()
image_ids = image_id_counts[image_id_counts == 3].index
grouped_surface = df[df.image_id.isin(image_ids) ].groupby(["image_id", "surface"]).size()

# same surface rating
round(100* len(grouped_surface[grouped_surface == 3]) / len(grouped_surface), 2)
# 70.62%
# TODO: Cohens kappa for interrater reliability
# df[df.image_id.isin(image_ids) ].to_csv("test.csv")

# where is it different?
#grouped_surface[grouped_surface != 3]


# same smoothness rating
grouped_smoothness = df[df.image_id.isin(image_ids) ].groupby(["image_id", "smoothness"]).size()
round(100* len(grouped_smoothness[grouped_smoothness == 3]) / len(grouped_smoothness), 2)
# 32.13%