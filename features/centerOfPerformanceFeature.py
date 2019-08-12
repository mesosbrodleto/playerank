from .abstract import Feature
from .wyscoutEventsDefinition import *
from pymongo import MongoClient
import json
from bson.code import Code

class centerOfPerformanceFeature(Feature):


    def createFeature(self, collectionName='centersOfPerformance', limit=None):

        """
        using matches collection to compute minutes played
        """

        client = MongoClient('localhost', 27017)
        db = client.wyscout_playerank

        non_goalkeepers_ids = [player['wyId'] for player in db.players.find({'role.name': {'$ne': 'Goalkeeper'}},
                                {'wyId': 1, 'role': 1}) if 'wyId' in player][:limit]
        MIN_EVENTS = 10

        pipeline = [

            { '$match' : { 'playerId' : {'$in': non_goalkeepers_ids}} },

            {'$project': {
                'matchId': 1,
                'playerId': 1,
                'positions': {'$arrayElemAt': ['$positions', 0]},
                'match_detail': 1
            }},

            {'$group': {
                '_id': {'match': {'match_id': '$matchId'}, 'player': {'player_id': '$playerId'}},
                'x_positions': {'$push': '$positions.x'},
                'y_positions': {'$push': '$positions.y'},
                'n_events': {'$sum': 1},
            }},

            { '$match' : { 'n_events' : {'$gte': MIN_EVENTS} } },

            {'$project':
             {

                '_id' :
                 {'player_info':{'player':'$_id.player.player_id','match':'$_id.match.match_id'},

                'data': [
                {'name': 'avg_x','value': {'$avg': "$x_positions"}},
                 {'name': 'avg_y','value': {'$avg': "$y_positions"}},
                 {'name': 'n_events','value': '$n_events'},
                 ]},

             }
            },
            {'$unwind':'$_id.data'},
            {'$project':
                {

                '_id': {'player':'$_id.player_info.player','match':'$_id.player_info.match',
                        'name':'$_id.data.name'},
                'value':'$_id.data.value',

                }
            },


            {'$out': 'centers_of_performance'},
        ]

        groups = db.events.aggregate(pipeline, allowDiskUse=True)
        return db.centers_of_performance
