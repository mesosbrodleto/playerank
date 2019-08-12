from .abstract import Aggregation
from .wyscoutEventsDefinition import *
import json
import pandas as pd
from collections import defaultdict

class plainAggregation(Aggregation):
    """
    merge features for each player and return a data frame
    match -> team (or entity) -> feature (playerank, timestamp, team, etc..)

    """
    def set_features(self,collection_list):
        self.collections=collection_list

    def get_features(self):
        return self.collections
    def set_aggregated_collection(self, collection):
        self.aggregated_collection = collection
    def get_aggregated_collection(self):
        return self.aggregated_collection
    def aggregate(self, to_dataframe = False):



        ###
        # prior to aggregation, we merge all the features collections
        featdata = []
        for collection in self.collections:
            featdata+=collection
            print ("[plainAggregation] added %s features"%len(collection))
        """
        single stage: transform aggregated feature per match into a collection of the form:
        match -> player -> {feature:value}
        """
        aggregated = defaultdict(lambda : defaultdict(dict))



        for document in featdata:
            match = document['match']
            entity = int(document['entity'])
            feature = document['feature']
            value = document['value']
            aggregated[match][entity].update({feature:value})

        result = []

        for match in aggregated:
            for entity in aggregated[match]:

                document = {'match':match,'entity':entity}
                document.update(aggregated[match][entity])
                result.append(document)


        print ("[plainAggregation] matches aggregated: %s"%len(result))
        if to_dataframe :


            df=pd.DataFrame(result).fillna(0)
            return df
        else:
            return result
