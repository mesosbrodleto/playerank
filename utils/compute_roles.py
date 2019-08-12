#import .models
from ..models import Clusterer

from ..features import centerOfPerformanceFeature, plainAggregation
import sys,json
#computing all quality features (passes accurate, passes failed, shots, etc.)

def compute_roleMatrix(output_path):
    #getting average position for each player in each match
    centerfeat = centerOfPerformanceFeature.centerOfPerformanceFeature()
    centerfeat = centerfeat.createFeature(events_path = 'playerank/data/events',
                        players_file='playerank/data/players.json')

    #plain aggregation to get a dataframe
    aggregation = plainAggregation.plainAggregation()
    aggregation.set_features([centerfeat])
    df = aggregation.aggregate(to_dataframe = True )

    #use clustering object to get the best fit
    clusterer = Clusterer.Clusterer(verbose=True, k_range=(8, 9))
    clusterer.fit(df.entity, df.match, df[['avg_x', 'avg_y']], kind='multi')

    matrix_role = clusterer.get_clusters_matrix(kind = 'multi')

    matrix_role = matrix_role
    json.dump(matrix_role,open(output_path,'w'))


compute_roleMatrix('playerank/conf/role_matrix.json')
