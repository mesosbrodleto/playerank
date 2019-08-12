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
        compute relative aggregation
        param

        - to_dataframe : return a dataframe instead of a list of documents

        """
        
        data = sum(self.collections, []) 
        teams = list(set([int(x['entity']) for x in data])) #selecting teamA e teamB as teams[0] and team[1]

        aggregated = defaultdict(lambda : defaultdict(lambda: defaultdict(int)))
        #format of aggregation: match,team,feature,valueTeam-valueOppositor
        result = []

        for document in data:
            match = document['match']
            entity = int(document['entity'])
            feature = document['feature']
            value = document['value']
            
            opponents = teams[0] if entity == teams[1] else teams[1]
            if feature == 'goal-scored':
                print document,opponents
            if feature in aggregated[match][opponents]: #feature present, inserting aggregation to result collection
                result_doc = {}
                result_doc['match'] = match
                result_doc['entity'] = entity
                result_doc[feature] = value - aggregated[match][entity][feature]
                result.append(result_doc) #adding teamA-teamB
                
                result_doc = {}
                result_doc['match'] = match
                result_doc['entity'] = opponents
                result_doc[feature] = aggregated[match][opponents][feature]-value
                result.append(result_doc) #adding teamB-teamA

            else : #feature not inserted, adding for successive processing
                aggregated[match][entity][feature] = value
        if to_dataframe :

            featList=[]
            for data in result:
                
                featList.append(data)
            df=pd.DataFrame(featList).fillna(0)
            print df.columns
            return df
        else:
            return result
