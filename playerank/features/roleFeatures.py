from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict

class roleFeatures(Feature):

    def set_features(self,collection_list):
        self.collections=collection_list

    def get_features(self):
        return self.collections
    def createFeature(self,matrix_role_file):
        """
        Given the matrix for roles, it computes, for each player and match,
        the role of a player

        A role matrix is a data structure where, given x and y (between 0 and 100),
        it contains the correspinding roles for a player having center of performance = x,y
        Role_matrix is computed within learning phase of playerank framework

        Input:
        role_matrix: file patch for dictionary in the format x->y->role
        feature_lists: lists of features for each player in each match, describing
                       players' average position

        """

        role_matrix = json.load(open(matrix_role_file,"r"))
        roles  = defaultdict(lambda: defaultdict(dict))
        for feature_list in self.get_features():
            for f in feature_list:
                roles[f['match']][f['entity']].update({f['feature']: f['value']})
        ## for each match and player we have
        ## avg_x,avg_y,n_events
        results = []
        for match in roles:
            for player in roles[match]:
                match_data = roles[match][player]
                role_label = role_matrix[str(match_data['avg_x'])][str(match_data['avg_y'])]
                #note: string conversion because loading role matrix from file does set everything as string
                document = {'match':match, 'entity':player, 'feature':'roleCluster','value':role_label}
                results.append(document)
        return results
