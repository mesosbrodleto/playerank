# /usr/local/bin/python
from collections import defaultdict, OrderedDict, Counter
import numpy as np
from scipy import optimize
from scipy.stats import gaussian_kde
#from utils import *
from sklearn.base import BaseEstimator
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score
from sklearn.dummy import DummyClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.feature_selection import RFECV
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.externals.joblib import Parallel, delayed
from sklearn.metrics.pairwise import pairwise_distances
from itertools import combinations
from sklearn.utils import check_random_state
from sklearn.preprocessing import MinMaxScaler
import json

def scalable_silhouette_score(X, labels, metric='euclidean', sample_size=None,
                           random_state=None, n_jobs=1, **kwds):
    """
    Compute the mean Silhouette Coefficient of all samples.
    The Silhouette Coefficient is compute using the mean intra-cluster distance (a)
    and the mean nearest-cluster distance (b) for each sample.

    The Silhouette Coefficient for a sample is $(b - a) / max(a, b)$.
    To clarify, b is the distance between a sample and the nearest cluster
    that b is not a part of.

    This function returns the mean Silhoeutte Coefficient over all samples.
    To obtain the values for each sample, it uses silhouette_samples.

    The best value is 1 and the worst value is -1. Values near 0 indicate
    overlapping clusters. Negative values generally indicate that a sample has
    been assigned to the wrong cluster, as a different cluster is more similar.

    Parameters
    ----------
    X : array [n_samples_a, n_features]
        the Feature array.

    labels : array, shape = [n_samples]
        label values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by metrics.pairwise.pairwise_distances. If X is the distance
        array itself, use "precomputed" as the metric.

    sample_size : int or None
        The size of the sample to use when computing the Silhouette
        Coefficient. If sample_size is None, no sampling is used.

    random_state : integer or numpy.RandomState, optional
        The generator used to initialize the centers. If an integer is
        given, it fixes the seed. Defaults to the global numpy random
        number generator.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    silhouette : float
        the Mean Silhouette Coefficient for all samples.

    References
    ----------
    Peter J. Rousseeuw (1987). "Silhouettes: a Graphical Aid to the
        Interpretation and Validation of Cluster Analysis". Computational
        and Applied Mathematics 20: 53-65. doi:10.1016/0377-0427(87)90125-7.
    http://en.wikipedia.org/wiki/Silhouette_(clustering)
    """
    if sample_size is not None:
        random_state = check_random_state(random_state)
        indices = random_state.permutation(X.shape[0])[:sample_size]
        if metric == "precomputed":
            raise ValueError('Distance matrix cannot be precomputed')
        else:
            X, labels = X[indices], labels[indices]

    return np.mean(scalable_silhouette_samples(
        X, labels, metric=metric, n_jobs=n_jobs, **kwds))


def scalable_silhouette_samples(X, labels, metric='euclidean', n_jobs=1, **kwds):
    """
    Compute the Silhouette Coefficient for each sample. The Silhoeutte Coefficient
    is a measure of how well samples are clustered with samples that are similar to themselves.
    Clustering models with a high Silhouette Coefficient are said to be dense,
    where samples in the same cluster are similar to each other, and well separated,
    where samples in different clusters are not very similar to each other.

    The Silhouette Coefficient is calculated using the mean intra-cluster
    distance (a) and the mean nearest-cluster distance (b) for each sample.

    The Silhouette Coefficient for a sample is $(b - a) / max(a, b)$.
    This function returns the Silhoeutte Coefficient for each sample.
    The best value is 1 and the worst value is -1. Values near 0 indicate
    overlapping clusters.

    Parameters
    ----------
    X : array [n_samples_a, n_features]
        Feature array.

    labels : array, shape = [n_samples]
        label values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by metrics.pairwise.pairwise_distances. If X is the distance
        array itself, use "precomputed" as the metric.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    silhouette : array, shape = [n_samples]
        Silhouette Coefficient for each samples.

    References
    ----------
    Peter J. Rousseeuw (1987). "Silhouettes: a Graphical Aid to the
        Interpretation and Validation of Cluster Analysis". Computational
        and Applied Mathematics 20: 53-65. doi:10.1016/0377-0427(87)90125-7.
    http://en.wikipedia.org/wiki/Silhouette_(clustering)
    """
    A = _intra_cluster_distances_block(X, labels, metric, n_jobs=n_jobs,
                                       **kwds)
    B = _nearest_cluster_distance_block(X, labels, metric, n_jobs=n_jobs,
                                        **kwds)
    sil_samples = (B - A) / np.maximum(A, B)
    # nan values are for clusters of size 1, and should be 0
    return np.nan_to_num(sil_samples)

def _intra_cluster_distances_block(X, labels, metric, n_jobs=1, **kwds):
    """
    Calculate the mean intra-cluster distance for sample i.

    Parameters
    ----------
    X : array [n_samples_a, n_features]
        Feature array.

    labels : array, shape = [n_samples]
        label values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by metrics.pairwise.pairwise_distances. If X is the distance
        array itself, use "precomputed" as the metric.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    a : array [n_samples_a]
        Mean intra-cluster distance
    """
    intra_dist = np.zeros(labels.size, dtype=float)
    values = Parallel(n_jobs=n_jobs)(
            delayed(_intra_cluster_distances_block_)
                (X[np.where(labels == label)[0]], metric, **kwds)
                for label in np.unique(labels))
    for label, values_ in zip(np.unique(labels), values):
        intra_dist[np.where(labels == label)[0]] = values_
    return intra_dist


def _nearest_cluster_distance_block(X, labels, metric, n_jobs=1, **kwds):
    """Calculate the mean nearest-cluster distance for sample i.

    Parameters
    ----------
    X : array [n_samples_a, n_features]
        Feature array.

    labels : array, shape = [n_samples]
        label values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by metrics.pairwise.pairwise_distances. If X is the distance
        array itself, use "precomputed" as the metric.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    X : array [n_samples_a, n_features]
        Feature array.

    Returns
    -------
    b : float
        Mean nearest-cluster distance for sample i
    """
    inter_dist = np.empty(labels.size, dtype=float)
    inter_dist.fill(np.inf)
    # Compute cluster distance between pairs of clusters
    unique_labels = np.unique(labels)

    values = Parallel(n_jobs=n_jobs)(
            delayed(_nearest_cluster_distance_block_)(
                X[np.where(labels == label_a)[0]],
                X[np.where(labels == label_b)[0]],
                metric, **kwds)
                for label_a, label_b in combinations(unique_labels, 2))

    for (label_a, label_b), (values_a, values_b) in \
            zip(combinations(unique_labels, 2), values):

            indices_a = np.where(labels == label_a)[0]
            inter_dist[indices_a] = np.minimum(values_a, inter_dist[indices_a])
            del indices_a
            indices_b = np.where(labels == label_b)[0]
            inter_dist[indices_b] = np.minimum(values_b, inter_dist[indices_b])
            del indices_b
    return inter_dist

def _intra_cluster_distances_block_(subX, metric, **kwds):
    distances = pairwise_distances(subX, metric=metric, **kwds)
    return distances.sum(axis=1) / (distances.shape[0] - 1)

def _nearest_cluster_distance_block_(subX_a, subX_b, metric, **kwds):
    dist = pairwise_distances(subX_a, subX_b, metric=metric, **kwds)
    dist_a = dist.mean(axis=1)
    dist_b = dist.mean(axis=0)
    return dist_a, dist_b

class Clusterer(BaseEstimator, ClusterMixin):
    """Performance clustering

    Parameters
    ----------
    k_range: tuple (pair)
        the minimum and the maximum $k$ to try when choosing the best value of $k$
        (the one having the best silhouette score)

    border_threshold: float
        the threshold to use for selecting the borderline.
        It indicates the max silhouette for a borderline point.

    verbose: boolean
        verbosity mode.
        default: False

    random_state : int
        RandomState instance or None, optional, default: None
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by `np.random`.

    sample_size : int
        the number of samples (rows) that must be used when computing the silhouette score (the function silhouette_score is computationally expensive and generates a Memory Error when the number of samples is too high)
        default: 10000

    max_rows : int
        the maximum number of samples (rows) to be considered for the clustering task (the function silhouette_samples is computationally expensive and generates a Memory Error when the input matrix have too many rows)
        default: 40000


    Attributes
    ----------
    cluster_centers_ : array, [n_clusters, n_features]
        Coordinates of cluster centers
    n_clusters_: int
        number of clusters found by the algorithm
    labels_ :
        Labels of each point
    k_range: tuple
        minimum and maximum number of clusters to try
    verbose: boolean
        whether or not to show details of the execution
    random_state: int
        RandomState instance or None, optional, default: None
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by 'np.random'.
    sample_size: None
    kmeans: scikit-learn KMeans object
    """

    def __init__(self, k_range=(2, 15), border_threshold=0.2, verbose=False, random_state=42,
                sample_size=None):
        self.k_range = k_range
        self.border_threshold = border_threshold
        self.verbose = verbose
        self.sample_size = sample_size
        # initialize attributes
        self.labels_ = []
        self.random_state = random_state

    def _find_clusters(self, X, make_plot=True):
        if self.verbose:
            print ('FITTING kmeans...\n')
            print ('n_clust\t|silhouette')
            print ('---------------------')

        self.k2silhouettes_ = {}
        kmin, kmax = self.k_range
        range_n_clusters = range(kmin, kmax + 1)
        best_k, best_silhouette = 0, 0.0
        for k in range_n_clusters:

            # computation
            kmeans = MiniBatchKMeans(n_clusters=k, init='k-means++', max_iter=100, n_init=1,
                               random_state =self.random_state)
            kmeans.fit(X)
            cluster_labels = kmeans.labels_

            silhouette = scalable_silhouette_score(X, cluster_labels,
                                          sample_size=self.sample_size,
                                          random_state=self.random_state)
            if self.verbose:
                print ('%s\t|%s' % (k, round(silhouette, 4)))

            if silhouette >= best_silhouette:
                best_silhouette = silhouette
                best_k = k
                #best_silhouette_samples = ss

            self.k2silhouettes_[k] = silhouette

        kmeans = MiniBatchKMeans(n_clusters=best_k, init='k-means++', max_iter=100, n_init=1,
                                 random_state=self.random_state)
        kmeans.fit(X)
        self.kmeans_ = kmeans
        self.n_clusters_ = best_k
        self.cluster_centers_ = kmeans.cluster_centers_
        self.labels_ = kmeans.labels_
        if self.verbose:
            print ('Best: n_clust=%s (silhouette=%s)\n' % (best_k, round(best_silhouette, 4)))

    def _cluster_borderline(self, X):
        """
        Assign clusters to borderline points, according to the borderline_threshold
        specified in the constructor
        """
        if self.verbose:
            print ('FINDING hybrid centers of performance...\n')

        self.labels_ = [[] for i in range(len(X))]

        ss = scalable_silhouette_samples(X, self.kmeans_.labels_)
        for i, (row, silhouette, cluster_label) in enumerate(zip(X, ss, self.kmeans_.labels_)):
            if silhouette >= self.border_threshold:
                self.labels_[i].append(cluster_label)
            else:
                intra_silhouette = euclidean(row, self.kmeans_.cluster_centers_[cluster_label])
                for label in set(self.kmeans_.labels_):
                    inter_silhouette = euclidean(row, self.kmeans_.cluster_centers_[label])
                    silhouette = (inter_silhouette - intra_silhouette) / max(inter_silhouette, intra_silhouette)
                    if silhouette <= self.border_threshold:
                        self.labels_[i].append(label)

        return ss

    def _generate_matrix(self, ss):
        """
        Generate a matrix for optimizing the predict function
        """
        matrix = {}
        X = []

        for i in range(0, 101):
            for j in range(0, 101):
                X.append([i, j])

        multi_labels = self._predict_with_silhouette(X, ss)
        for row, labels in zip(X, multi_labels):
            matrix[tuple(row)] = labels
        self._matrix = matrix

    def get_clusters_matrix(self, kind = 'single'):
        roles_matrix = {}
        if kind != 'single':
            m= self._matrix.items()

        else:
            m = self._matrix_single.items()
        for k,v in  m:
            x,y = int(k[0]),int(k[1])
            if k[0] not in roles_matrix:
                roles_matrix[x] = {}
            roles_matrix[x][y] = "-".join(map(str,v)) if kind !='single' else int(v) #casting with python int, otherwise it's not json serializable
        return roles_matrix

    def fit(self, player_ids, match_ids, dataframe, y=None, kind='single', filename='clusters'):
        """
        Compute performance clustering.

        Parameters
        ----------
            X : array-like or sparse matrix, shape=(n_samples, n_features)
            Training instances to cluster.

            kind: str
                single: single cluster
                multi: multi cluster

            y: ignored
        """
        self.kind_ = kind
        X = dataframe.values

        self._find_clusters(X)      # find the clusters with kmeans
        if kind == 'single':
            players_and_matches_and_roles = []
            for player_id, match_id, label in zip(player_ids, match_ids, self.labels_):
                players_and_matches_and_roles.append({'player_id': player_id, 'match_id': match_id, 'role': int(label)})
            json.dump(players_and_matches_and_roles, open('%s.json' %filename, 'w'))
            return self

        silhouette_scores = self._cluster_borderline(X) # assign multiclusters to borderline performances
        self._generate_matrix(silhouette_scores)    # generate the matrix for optimizing the predict function
        if self.verbose:
            print ("DONE.")




        return self

    def _predict_with_silhouette(self, X, ss):
        cluster_labels, threshold = self.kmeans_.predict(X), self.border_threshold
        multicluster_labels = [[] for _ in cluster_labels]
        if len(set(cluster_labels)) == 1:
            return [[cluster_label] for cluster_label in cluster_labels]
        for i, (row, silhouette, cluster_label) in enumerate(zip(X, ss, cluster_labels)):
            if silhouette >= threshold:
                multicluster_labels[i].append(cluster_label)
            else:
                intra_silhouette = euclidean(row, self.cluster_centers_[cluster_label])
                for label in set(cluster_labels):
                    inter_silhouette = euclidean(row, self.cluster_centers_[label])
                    silhouette = (inter_silhouette - intra_silhouette) / max(inter_silhouette, intra_silhouette)
                    if silhouette <= threshold:
                        multicluster_labels[i].append(label)

        return np.array(multicluster_labels)

    def predict(self, X, y=None):
        """
        Predict the closest cluster each sample in X belongs to.
        In the vector quantization literature, `cluster_centers_` is called
        the code book and each value returned by `predict` is the index of
        the closest code in the code book.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape = [n_samples, n_features]
            New data to predict.

        Returns
        -------
        multi_labels : array, shape [n_samples,]
            Index of the cluster each sample belongs to.
        """
        if self.kind_ == 'single':
            return self.kmeans_predict(X)
        else:
            multi_labels = []
            for row in X:
                x, y = tuple(row)
                labels = self._matrix[(int(x), int(y))]
                multi_labels.append(labels)
            return multi_labels
