# /usr/local/bin/python
import pickle as pkl
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.utils import check_random_state
from sklearn.preprocessing import MinMaxScaler
import json

class Weighter(BaseEstimator):
    """Automatic weighting of performance features

    Parameters
    ----------
    label_type: str
        the label type associated to the game outcome.
        options: w-dl (victory vs draw or defeat), wd-l (victory or draw vs defeat),
                 w-d-l (victory, draw, defeat)
    random_state : int
        RandomState instance or None, optional, default: None
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by `np.random`.

    Attributes
    ----------
    feature_names_ : array, [n_features]
        names of the features
    label_type_: str
        the label type associated to the game outcome.
        options: w-dl (victory vs draw or defeat), wd-l (victory or draw vs defeat),
                 w-d-l (victory, draw, defeat)
    clf_: LinearSVC object
        the object of the trained classifier
    weights_ : array, [n_features]
        weights of the features computed by the classifier
    random_state_: int
        RandomState instance or None, optional, default: None
        If int, random_state is the seed used by the random number generator;
        If RandomState instance, random_state is the random number generator;
        If None, the random number generator is the RandomState instance used
        by 'np.random'.
    """
    def __init__(self, label_type='w-dl', random_state=42):
        self.label_type_ = label_type
        self.random_state_ = random_state

    def fit(self, dataframe, target, scaled=False, filename='weights.json'):
        """
        Compute weights of features.

        Parameters
        ----------
            dataframe : pandas DataFrame
                a dataframe containing the feature values and the target values

            target: str
               a string indicating the name of the target variable in the dataframe

            scaled: boolean
                True if X must be normalized, False otherwise
                (optional)

            filename: str
                the name of the files to be saved (the json file containing the feature weights,
                )
                default: "weights"
        """
        if self.label_type_ == 'w-dl':
            y = dataframe[target].apply(lambda x: 1 if x > 0 else -1)
        elif self.label_type_ == 'wd-l':
            y = dataframe[target].apply(lambda x: 1 if x >= 0 else -1 )
        else:
            y = dataframe[target].apply(lambda x: 1 if x > 0 else 0 if x==0 else 2)
        X = dataframe.loc[:, dataframe.columns != target].values
        y = y.values

        if scaled:
            X = StandardScaler().fit_transform(X)

        self.feature_names_ = dataframe.columns
        self.clf_ = LinearSVC(fit_intercept=True, dual = False,  max_iter = 50000,random_state=self.random_state_)

        #f1_score = np.mean(cross_val_score(self.clf_, X, y, cv=2, scoring='f1_weighted'))
        #self.f1_score_ = f1_score

        self.clf_.fit(X, y)

        outcome = 0
        if self.label_type_ == 'w-d-l':
            outcome = 1

        importances = self.clf_.coef_[outcome]

        sum_importances = sum(np.abs(importances))
        self.weights_ = importances / sum_importances

        ## Save the computed weights into a json file
        features_and_weights = {}
        for feature, weight in sorted(zip(self.feature_names_, self.weights_),key = lambda x: x[1]):
            features_and_weights[feature]=  weight
        json.dump(features_and_weights, open('%s' %filename, 'w'))
        ## Save the object
        #pkl.dump(self, open('%s.pkl' %filename, 'wb'))

    def get_weights(self):
        return self.weights_

    def get_feature_names(self):
        return self.feature_names_
