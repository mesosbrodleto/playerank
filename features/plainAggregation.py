from .abstract import Aggregation
from .wyscoutEventsDefinition import *
from pymongo import MongoClient
from bson.code import Code
import json
import pandas as pd

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
    def aggregate(self, to_dataframe = False, stored_collection_name = 'playerPerformanceFeatures'):
        """
        parameters:
        keepFeatureKeys: add the aggregation keys (e.g. (match,playerid)) to the output dataframe
        """
        client = MongoClient('localhost', 27017)
        db = client.wyscout_playerank

        ###
        # prior to aggregation, we merge all the features collections
        mapToMerge= Code("""function(){ emit({'match':this._id.match,'player':this._id.player,'name':this._id.name},this.value);}""")

        reducer_merge = Code(""" //only to ensure of returning the same value (avoiding multiple call of reducer)
                function (key, values) {
                   return values[0]; //value is a string


                }
        """)
        db.mergedFeatures.delete_many({})
        for collection in self.collections:
            collection.map_reduce(mapToMerge,reducer_merge,out={'reduce':'mergedFeatures'})
        print (db.mergedFeatures.find_one())
        """
        single stage: transform aggregated feature per match into a collection of the form:
        match -> player -> {feature:value}
        """

        pipeline=[{'$group': {"_id":{'match':"$_id.match",'player':'$_id.player'}, #group all features by match,entity
                              "values":{'$push':{'k':'$_id.name','v':'$value'}}}},
                  {'$project':{'_id':1,'values':{ '$arrayToObject': "$values" }}},

                  {'$out':stored_collection_name}
        ]

        relative_quality=db.mergedFeatures.aggregate(pipeline=pipeline,allowDiskUse=True)
        self.set_aggregated_collection(db[stored_collection_name])
        if to_dataframe :

            featList=[]
            for x in list(db[stored_collection_name].find({})):
                data=x['_id']
                data.update(x['values'])
                featList.append(data)
            df=pd.DataFrame(featList).fillna(0)
            return df
        else:
            return self.get_aggregated_collection()
