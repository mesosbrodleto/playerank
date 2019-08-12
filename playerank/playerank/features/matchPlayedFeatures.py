from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
import glob


class matchPlayedFeatures(Feature):

    def createFeature(self,matches_path,players_file,select = None):
        """
        It computes, for each player and match, total time (in minutes) played,
        goals scored and


        Input:
        -matches_path: folder with json files corresponding to matches data
        -select: function  for filtering matches collection. Default: aggregate over all matches

        Output:

        a collection of documents in the f
        ormat _id-> {'match': this.wyId, 'player' : player,
        'name': 'minutesPlayed'|'team'|'goalScored'|'timestamp'},value: <float>|<string>;

        """
        players =  json.load(open(players_file))
        #  filtering out all the events from goalkeepers
        goalkeepers_ids = [player['wyId'] for player in players
                                if player['role']['name']=='Goalkeeper']
        matches= []
        for file in glob.glob("%s/*.json"%matches_path):
            matches += json.load(open(file))
        if select:
            matches = filter(select,matches)

        print ("[matchPlayedFeatures] processing %s matches"%len(matches))
        result = []
        for match in matches:
            matchId= match['wyId']
            duration = 90
            if match['duration'] != 'Regular':
                duration = 120

            timestamp = match['dateutc']

            for team in match['teamsData']:
                minutes_played = {}
                goals_scored = {}
                if 'substitutions' in match['teamsData'][team]['formation']:
                    for sub in match['teamsData'][team]['formation']['substitutions']:
                        if type(sub) == dict:
                            minute = sub['minute']
                            minutes_played[sub['playerOut']] = minute
                            minutes_played[sub['playerIn']] = duration - minute
                if 'lineup' in match['teamsData'][team]['formation']:
                    for player in match['teamsData'][team]['formation']['lineup']:
                        goals_scored[player['playerId']] = player['goals']
                        if player['playerId'] not in minutes_played:
                            #player not substituted
                            minutes_played[player['playerId']] = duration
                if 'bench' in match['teamsData'][team]['formation']:
                    for player in match['teamsData'][team]['formation']['bench']:
                        goals_scored[player['playerId']] = player['goals']
                        if player['playerId'] not in minutes_played:
                            #player not substituted
                            minutes_played[player['playerId']] = duration
                for player,min in minutes_played.items():
                    if player not in goalkeepers_ids:
                        document = {'match':matchId,'entity':player,'feature':'minutesPlayed',
                                'value': min}
                        result.append (document)

                for player,gs in goals_scored.items():
                    if player not in goalkeepers_ids:
                        document = {'match':matchId,'entity':player,'feature':'goalScored',
                                'value': gs}
                        result.append (document)
                        ## adding timestamp and team for each player
                        document = {'match':matchId,'entity':player,'feature':'timestamp',
                            'value': timestamp}

                        result.append (document)
                        ## adding timestamp and team for each player
                        document = {'match':matchId,'entity':player,'feature':'team',
                                'value': team}
                        result.append (document)
        print ("[matchPlayedFeatures] matches features computed. %s features processed"%(len(result)))
        return result
