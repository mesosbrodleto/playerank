from ..models import Weighter

from ..features import playerankFeatures, plainAggregation, matchPlayedFeatures,roleFeatures
import sys,json 

weigths_file = sys.argv[1]
prFeat = playerankFeatures.playerankFeatures()

pr= prFeat.createFeature(weigths_file,param={'competitionId': 524},limit = 5)

print ("PlayeRank Score Computed. \n %s performance processed"%pr.count())
mFeat= matchPlayedFeatures.matchPlayedFeatures()

mins= mFeat.createFeature(param={'competitionId': 524})

matrix_role = json.load(open('playerlib/conf/role_matrix.json'))
roleFeat = roleFeatures.roleFeatures()

roles= roleFeat.createFeature(matrix_role, param={'competitionId': 524})

aggregation = plainAggregation.plainAggregation()

aggregation.set_features([mins,pr])

df = aggregation.aggregate(to_dataframe = True, stored_collection_name = 'playerank_scores')

df.to_csv('playerank.csv') 
