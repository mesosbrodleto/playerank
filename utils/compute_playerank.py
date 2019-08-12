from ..models import Weighter

from ..features import centerOfPerformanceFeature,qualityFeatures,playerankFeatures, plainAggregation, matchPlayedFeatures,roleFeatures
import sys,json

weigths_file ='playerank/conf/features_weights.json'

qualityFeat = qualityFeatures.qualityFeatures()
quality= qualityFeat.createFeature(events_path = 'playerank/data/events',
                    players_file='playerank/data/players.json' ,entity = 'player')


prFeat = playerankFeatures.playerankFeatures()
prFeat.set_features([quality])
pr= prFeat.createFeature(weigths_file)


matchPlayedFeat = matchPlayedFeatures.matchPlayedFeatures()
matchplayed = matchPlayedFeat.createFeature(matches_path = 'playerank/data/matches',
                    players_file='playerank/data/players.json' )

center_performance = centerOfPerformanceFeature.centerOfPerformanceFeature()

center_performance = center_performance.createFeature(events_path = 'playerank/data/events',
                                        players_file = 'playerank/data/players.json' )


roleFeat = roleFeatures.roleFeatures()
roleFeat.set_features([center_performance])
roles= roleFeat.createFeature(matrix_role_file = 'playerank/conf/role_matrix.json')


aggregation = plainAggregation.plainAggregation()

aggregation.set_features([matchplayed,pr,roles])

df = aggregation.aggregate(to_dataframe = True)

print (df.head())
