from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict
import glob


class goalScoredFeatures(Feature):
    """
    goals scored by each team in each match
    """
    def createFeature(self,matches_path,select = None):
        """
        stores qualityFeatures on database
        parameters:
        -matches_path: file path of matches file
        -select: function  for filtering matches collection. Default: aggregate over all matches

        Output:
        list of documents in the format: match: matchId, entity: team, feature: feature, value: value
        """
        matches =[]
        for file in glob.glob("%s"%matches_path):
            data = json.load(open(file))
            matches += data
            print ("[GoalScored features] added %s matches"%len(data))
        if select:
            matches = filter(select,matches)
        result =[]

        for match in matches:
            for team in match['teamsData']:
                document = {}
                document['match'] = match['wyId']
                document['entity'] = team
                document['feature'] = 'goal-scored'
                document['value'] = match['teamsData'][team]['score']
                result.append(document)


        return result
