from .abstract import Aggregation
from .wyscoutEventsDefinition import *
import json
import pandas as pd
from collections import defaultdict

class relativeAggregation(Aggregation):
    """
    compute relative feature for each match
    match -> team (or entity) -> featureTeam - featureOpponents
    """
    def set_features(self,collection_list):
        self.collections=collection_list

    def get_features(self):
        return self.collections
    def aggregate(self,to_dataframe = False):
        """
        compute relative aggregation: give a set of features it compute the A-B
        value for each entity in each team.
        Ex:
        passes for team A in match 111 : 500
        passes for team B in match 111 : 300
        lead to output:
        {'passes': 200}

        this method is involved for feature weight estimation phase of playerank framework.
        param

        - to_dataframe : return a dataframe instead of a list of documents

        """

        featdata = []
        for collection in self.collections:
            featdata+=collection
            print ("[relativeAggregation] added %s features"%len(collection))
        #selecting teamA e teamB as teams[0] and team[1]
        aggregated = defaultdict(lambda : defaultdict(lambda: defaultdict(int)))
        #format of aggregation: match,team,feature,valueTeam-valueOppositor
        result = []
        for document in featdata:
            match = document['match']
            entity = int(document['entity'])
            feature = document['feature']
            value = document['value']
            aggregated[match][entity][feature] = int(value)


        for match in aggregated:
            for entity in aggregated[match]:
                for feature in aggregated[match][entity]:
                    opponents = [x for x in aggregated[match] if x!=entity][0]

                    result_doc = {}
                    result_doc['match'] = match
                    result_doc['entity'] = entity
                    result_doc['name'] = feature
                    value = aggregated[match][entity][feature]
                    if feature in aggregated[match][opponents]:
                        result_doc['value'] = value - aggregated[match][opponents][feature]
                    else:
                        result_doc['value'] = value
                    result.append(result_doc)

        if to_dataframe :

            featlist = defaultdict(dict)
            for data in result:

                featlist["%s-%s"%(data['match'],data['entity'])].update({data['name']:data['value']})
            print ("[relativeAggregation] matches aggregated: %s"%len(featlist.keys()))

            df=pd.DataFrame(list(featlist.values())).fillna(0)

            return df
        else:
            return result
