import os
import json
from pprint import pprint

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from common.utils.files import load_file


"""
There is 2 main tasks in this step
1- text clustering
    - blind clustering -> 
            it discard the meaning and compare vectors of words together
            using -> K-means, Hierarchical Clustering, DBSCAN
            # K-mean clustering
            ## Elbow method to know how many clusters are there

    - cluster with context ->
            should use AI for understanding the text

2- labels the cluster (2 types)
    - ai with predefined labels and use one-shot-model 
    - ai without predefined
    - manual labels
        * website name
        * and the most repeated word in the documents 
        * or whatever algorithm
"""


def get_paths() -> list[str]:
    DIR = './resources/documents/'
    fname = lambda i: int(i.split('/')[-1].split('.')[0].strip('+')) # get filename

    files = os.listdir(DIR)
    files = filter(lambda f: f.endswith('+.json'), files)
    files = map(lambda f: DIR + f, files)
    files = list(files)
    files = sorted(files, key=fname)

    return files


files = get_paths()

documents = map(load_file, files)
documents = map(json.loads, documents)
documents = tuple(documents)


unique_words = list(set(word for doc in documents for word in doc))

weights_matrix = np.zeros((len(documents), len(unique_words)))

for i, doc in enumerate(documents):
    for j, word in enumerate(unique_words):
        weights_matrix[i, j] = doc.get(word, 0.0)

cosine_similarities = cosine_similarity(weights_matrix)
cosine_similarities = cosine_similarities.round(2)

# df = pd.DataFrame(cosine_similarities)
# df.to_csv("file.csv")

print(len(unique_words))
# print(cosine_similarities)

sims = {}
for doc_name, doc_sims in zip(files, cosine_similarities):
    sims[doc_name] = []
    for f, sim in zip(files, doc_sims):
        if doc_name == f: continue
        if sim > 0.4:
            sims[doc_name].append((sim, f))
        

pprint(sims)    


# print(mx)






