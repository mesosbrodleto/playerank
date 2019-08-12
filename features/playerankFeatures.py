from .abstract import Feature
from .wyscoutEventsDefinition import *
from pymongo import MongoClient
import json
from bson.code import Code


class playerankFeatures(Feature):
    """
    Given a method to aggregate features and the corresponding weight of each feature,
    it computes playerank for each player ad match
    output: 
    a collection of documents in the format: _id -> {match:match_id, name: 'playerankScore', player:player_id}, value-> playerankScore(float)
    """
    def createFeature(self,weights_file,collectionName='playerankFeatures',param={},goal_weight=0,limit=None):


        client = MongoClient('localhost', 27017)
        db = client.wyscout_playerank

        players={x['wyId']:x['shortName'] for x in
         list(db.players.find({},{'wyId':1,'shortName':1})) if 'shortName' in x}
        players[0]='0'

        ### to be added to the scope of Playerank computing function
        str_players="""function(){var data=%s; return data;}"""%json.dumps(players)
        weights=json.load(open(weights_file))
        weights['GOAL']=goal_weight
        str_weights="var w=%s; return w;"%json.dumps(weights)
        str_macro2name="""function(){var data=%s; return data;}"""%json.dumps(macroevent2name)
        str_subevent2name="""function(){var data=%s; return data;}"""%json.dumps(subevents2name)
        str_tag2name="""function(){var data=%s; return data;}"""%json.dumps(tag2name)
        ###
        match_playeRank = Code(
        """
        function ()
        {
                var teamId=this.teamId;
                var subEventId=this.subEventId
                var playerId=this.playerId;
                var eventId=this.eventId;
                var matchId=this.matchId;
                var macroName=macro2name();
                var subName=sub2name();
                var tagName=tag2name();
                var weights=weight();
                var player_names=players();
                if (playerId != 0) {
                    if (playerId in player_names) playerId = player_names[playerId];

                    if (this.tags.length>0)
                    {
                        this.tags.forEach(function(e)
                        {
                            var name=macroName[eventId] + '-' + subName[subEventId] + '-' + tagName[e.id];

                            if (tagName[e.id]=='GOAL') name = 'GOAL'; //to use goal weight

                            if (name in weights)
                            {
                                var w= weights[name];
                                emit({'match':matchId, 'name': 'playerankScore', 'player': playerId}, w);
                            }
                        });
                    }
                    else
                    {
                        var name=macroName[eventId] + '-' + subName[subEventId];
                        if (name in weights)
                        {
                            var w= weights[name];
                            emit({'match': matchId,'name':'playerankScore','player': playerId}, w);
                        }
                    }
                }



        }
        """)
        #reduce -> sum features for each team, player, feature
        reducer_sum = Code("""
                    function (key, values) {
                      var total = 0;
                      for (var i = 0; i < values.length; i++) {
                        total += values[i];
                      }
                      return total;
                    }
                    """)

        matches = [x['wyId'] for x in db.matches.find(param,{'wyId':1})][:limit]
        query={'matchId':{'$in': matches},"subEventId": {"$exists":1}}
        result_playeRank=db.events.map_reduce(match_playeRank,reducer_sum,collectionName,
                query=query,
                scope={'macro2name':Code(str_macro2name),'sub2name':Code(str_subevent2name),
                    'tag2name':Code(str_tag2name), 'weight':Code(str_weights), 'players':Code(str_players)})

        return result_playeRank
