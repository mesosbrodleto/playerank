from .abstract import Feature
from .wyscoutEventsDefinition import *
from collections import defaultdict
import json


class playerankFeatures(Feature):
    """
    Given a method to aggregate features and the corresponding weight of each feature,
    it computes playerank for each player and match
    input:
    -- features weights, computed within learning phase of playerank framework

    output:
    -- a collection of json documents in the format:
       {match:match_id, name: 'playerankScore', player:player_id,
       value: playerankScore(float)}
    """
    def set_features(self,collection_list):
        self.collections=collection_list

    def get_features(self):
        return self.collections
    def createFeature(self,weights_file):

        weights=json.load(open(weights_file))
        playerank_scores = defaultdict(lambda: defaultdict(float))
        for feature_list in self.get_features():
            for f in feature_list:
                playerank_scores[f['match']][f['entity']]+=f['value']*weights[f['feature']]

        result = []
        for match in playerank_scores:
            for player in playerank_scores[match]:
                document = {
                    'match': match,
                    'entity': player,
                    'feature' : 'playerankScore',
                    'value' : playerank_scores[match][player]
                }
                result.append(document)
        print ("[playerankFeatures] playerank scores computed. %s performance processed"%len(result))
        return result
