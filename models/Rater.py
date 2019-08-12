# /usr/local/bin/python
import cPickle as pkl
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

class Rater():
    """Performance rating

    Parameters
    ----------
    alpha_goal: float
        importance of the goal in the evaluation of performance, in the range [0, 1]
        default=0.0

    Attributes
    ----------
    ratings_: numpy array
        the ratings of the performances
    """
    def __init__(self, feature2weight, alpha_goal=0.0):
        self.feature2weight = feature2weight
        self.alpha_goal = alpha_goal
        self.ratings_ = []
    
    def get_rating(self, weighted_sum, goals):
        return weighted_sum * (1 - self.alpha_goal) + self.alpha_goal * goals
  
    def predict(self, dataframe, goal_feature, filename='ratings'):
        """
        Compute the rating of each performance in X
        
        Parameters
        ----------
        X: numpy array
        
        feature_names: list
            list of feature names
        
        Returns
        -------
        ratings_: numpy array
        """
        feature_names = dataframe.columns
        X = dataframe.values
        
        for i, row in enumerate(X):
            weighted_sum = sum([float(row[j]) * float(self.feature2weight[feature]) for j, feature in enumerate(feature_names) if feature != goal_feature])
            goal_index = feature_names.index(goal_feature)
            rating = self.get_rating(weighted_sum, row[goal_index])
            self.ratings_.append(rating)
        self.ratings_ = MinMaxScaler().fit_transform(np.array(self.ratings_).reshape(-1, 1))[:, 0]
        
        dataframe['playeratings'] = self.ratings_
        dataframe.to_json(filename, orient='records')
        
        return self.ratings_  
    