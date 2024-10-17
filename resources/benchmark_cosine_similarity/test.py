import time

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Generating a random matrix of shape (10000, 10000)
X = np.random.rand(10000, 10000)

start = time.time()
# Calculating cosine similarity
similarity_matrix = cosine_similarity(X)

print(time.time() - start)
