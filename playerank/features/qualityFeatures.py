from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict
import glob


class qualityFeatures(Feature):
    """
    Quality features are the count of events with outcomes.
    E.g.
    - number of accurate passes
    - number of wrong passes
    ...
    """
    def createFeature(self,events_path,players_file,entity = 'team',select = None):
        """
        compute qualityFeatures
        parameters:
        -events_path: file path of events file
        -select: function  for filtering events collection. Default: aggregate over all events
        -entity: it could either 'team' or 'player'. It selects the aggregation for qualityFeatures among teams or players qualityfeatures

        Output:
        list of dictionaries in the format: matchId -> entity -> feature -> value
        """
        event2subevent2outcome={
                1:{10: [1801, 1802],
                 11: [1801, 1802],
                 12: [1801, 1802],
                 13: [1801, 1802]},
                 2: [1702, 1703, 1701], #fouls aggregated into macroevent

                 3 :{30: [1801, 1802],
                 31: [1801, 1802],
                 32: [1801, 1802],
                 33: [1801, 1802],
                 34: [1801, 1802],
                 35: [1802],
                 36: [1801, 1802]},
                 4: {40: [1801, 1802]},
                 6: {60: []},
                 7: {70: [1801, 1802,101],
                 71: [1801, 1802,101],
                 72: [1401, 1302, 201, 1901, 1301, 2001, 301]},
                 8: {80: [1801, 1802,302,301],
                 81: [1801, 1802,302,301],
                 82: [1801, 1802,302,301],
                 83: [1801, 1802,302,301],
                 84: [1801, 1802,302,301],
                 85: [1801, 1802,302,301],
                 86: [1801, 1802,302,301]},
                 #90: [1801, 1802],
                 #91: [1801, 1802],
                 10: {100: [1801, 1802]}}

        aggregated_features = defaultdict(lambda : defaultdict(lambda: defaultdict(int)))

        players =  json.load(open(players_file))
        #  filtering out all the events from goalkeepers
        goalkeepers_ids = [player['wyId'] for player in players
                                if player['role']['name']=='Goalkeeper']

        events = []
        for file in glob.glob("%s/*.json"%events_path):
            data = json.load(open(file))
            if select:
                data = list(filter(select,data))
            events += list(filter(lambda x: x['matchPeriod'] in ['1H','2H'] and x['playerId'] not in  goalkeepers_ids,data)) #excluding penalties events
            print ("[qualityFeatures] added %s events from %s"%(len(data), file))
        

        for evt in events:
            if evt['eventId'] in event2subevent2outcome:
                ent = evt['teamId'] #default
                if entity == 'player':
                    ent = evt['playerId']

                evtName =evt['eventName']

                if type(event2subevent2outcome[evt['eventId']]) == dict:
                    #hierarchy as event->subevent->tags
                    if evt['subEventId'] not in event2subevent2outcome[evt['eventId']]:
                        #malformed events
                        continue #skip to next event
                    tags = [x for x in evt['tags'] if x['id'] in event2subevent2outcome[evt['eventId']][evt['subEventId']]]

                    evtName+="-%s"%evt['subEventName']
                else:
                    #hierarchy as event->tags
                    tags = [x for x in evt['tags'] if x['id'] in event2subevent2outcome[evt['eventId']]]

                if len(tags)>0:
                    for tag in tags:
                        aggregated_features[evt['matchId']][ent]["%s-%s"%(evtName,tag2name[tag['id']])]+=1

                else:
                    aggregated_features[evt['matchId']][ent]["%s"%(evtName)]+=1
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
