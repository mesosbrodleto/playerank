#import .models
from ..models import Weighter

from ..features import qualityFeatures, relativeAggregation,goalScoredFeatures

def compute_feature_weights(output_path):

    qualityFeat = qualityFeatures.qualityFeatures()
    quality= qualityFeat.createFeature(events_path = 'playerank/data/events',
                        players_file='playerank/data/players.json' ,entity = 'team')
    #computing goals scored for each team in each match
    gs=goalScoredFeatures.goalScoredFeatures()
    goals=gs.createFeature('playerank/data/matches')
    #merging of quality features and goals scored
    aggregation = relativeAggregation.relativeAggregation()
    aggregation.set_features([quality,goals])
    df = aggregation.aggregate(to_dataframe = True)

    weighter = Weighter.Weighter(label_type='wd-l')
    weighter.fit(df, 'goal-scored', filename=output_path)
    print ("features weights stored in %s"%output_path)


compute_feature_weights('playerank/conf/features_weights.json')
