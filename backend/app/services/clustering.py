import numpy as np
from typing import Tuple
from sklearn.cluster import HDBSCAN, KMeans

def cluster_embeddings(
    embeddings: np.ndarray,
    min_cluster_size: int = 3,
    min_samples: int = 2
) -> np.ndarray:
    """
    Clusters review embeddings using HDBSCAN with an adaptive KMeans fallback.
    Returns:
        labels: 1D np.ndarray of integer cluster IDs (0 to num_clusters - 1)
    """
    n_samples = len(embeddings)
    if n_samples == 0:
        return np.array([], dtype=int)
    if n_samples == 1:
        return np.zeros(1, dtype=int)

    # If dataset is very small, use KMeans with 2 or 3 clusters
    if n_samples < 6:
        k = min(2, n_samples)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        return kmeans.fit_predict(embeddings)

    # Attempt HDBSCAN
    try:
        # Cosine distance = 1 - cosine_similarity for normalized embeddings
        clusterer = HDBSCAN(
            min_cluster_size=min(min_cluster_size, max(2, n_samples // 4)),
            min_samples=min(min_samples, max(1, n_samples // 8)),
            metric="euclidean"
        )
        labels = clusterer.fit_predict(embeddings)
        unique_labels = set(labels)
        
        # Count non-noise clusters
        non_noise_clusters = [lbl for lbl in unique_labels if lbl != -1]
        noise_count = np.sum(labels == -1)

        # If HDBSCAN found at least 2 clusters and noise is < 50%, reassign noise points
        if len(non_noise_clusters) >= 2 and (noise_count / n_samples) < 0.6:
            centroids = {}
            for c in non_noise_clusters:
                centroids[c] = np.mean(embeddings[labels == c], axis=0)

            # Reassign noise points (-1) to the nearest cluster centroid
            for idx in np.where(labels == -1)[0]:
                vec = embeddings[idx]
                best_cluster = min(
                    non_noise_clusters,
                    key=lambda c: np.linalg.norm(vec - centroids[c])
                )
                labels[idx] = best_cluster

            # Re-index labels from 0 to N-1
            cluster_map = {old: new for new, old in enumerate(sorted(set(labels)))}
            return np.array([cluster_map[lbl] for lbl in labels], dtype=int)

    except Exception as e:
        print(f"[Clustering] HDBSCAN failed, falling back to KMeans: {e}")

    # Fallback: Adaptive KMeans
    # Rule of thumb: sqrt(N/2), bounded between 2 and 15
    k = max(2, min(int(np.sqrt(n_samples / 2)), 12))
    k = min(k, n_samples)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(embeddings)
    return labels
