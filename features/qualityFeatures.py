from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict


class qualityFeatures(Feature):
    """
    Quality features are the count of events with outcomes.
    E.g.
    - number of accurate passes
    - number of wrong passes
    ...
    """
    def createFeature(self,events_path,entity = 'team',select = None):
        """
        compute qualityFeatures
        parameters:
        -events_path: file path of events file
        -select: function  for filtering matches collection. Default: aggregate over all matches
        -entity: it could either 'team' or 'player'. It selects the aggregation for qualityFeatures among teams or players qualityfeatures

        Output:
        list of dictionaries in the format: matchId -> entity -> feature -> value
        """
        subevent2outcome = {10: [1801, 1802],
             11: [1801, 1802],
             12: [1801, 1802],
             13: [1801, 1802],
             20: [1702, 1703, 1701],
             21: [1702, 1703, 1701],
             22: [1702, 1703, 1701],
             23: [1702, 1703, 1701],
             24: [1702, 1703, 1701],
             25: [1702, 1703, 1701],
             27: [1702, 1703, 1701],
             30: [1801, 1802],
             31: [1801, 1802],
             32: [1801, 1802],
             33: [1801, 1802],
             34: [1801, 1802],
             35: [1802],
             36: [1801, 1802],
             40: [1801, 1802],
             60: [],
             70: [1801, 1802,101],
             71: [1801, 1802,101],
             72: [1401, 1302, 201, 1901, 1301, 2001, 301],
             80: [1801, 1802,302],
             81: [1801, 1802,302],
             82: [1801, 1802,302],
             83: [1801, 1802,302],
             84: [1801, 1802,302],
             85: [1801, 1802,302],
             86: [1801, 1802,302],
             90: [1801, 1802],
             91: [1801, 1802],
             100: [1801, 1802]}
            
        aggregated_features = defaultdict(lambda : defaultdict(lambda: defaultdict(int)))
        events = json.load(open(events_path))
        if select:
            events = filter(select,events)
        for evt in events:
            if evt['subEventId'] in subevent2outcome:
                ent = evt['teamId'] #default
                if entity == 'player':
                    ent = evt['playerId']
                tags = [x for x in evt['tags'] if x in subevent2outcome[evt['subEventId']]]
                if len(tags)>0:
                    for tag in tags:
                        aggregated_features[evt['matchId']][ent]["%s-%s-%s"%(evt['eventName'],evt['subEventName'],tag2name[tag['id']])]+=1
                        
                else:
                    aggregated_features[evt['matchId']][ent]["%s-%s"%(evt['eventName'],evt['subEventName'])]+=1
        result =[]
        for match in aggregated_features:
            for entity in aggregated_features[match]:
                for feature in aggregated_features[match][entity]:
                    document = {}
                    document['match'] = match
                    document['entity'] = entity
                    document['feature'] = feature
                    document['value'] = aggregated_features[match][entity][feature]
                    result.append(document)
                    
        return result