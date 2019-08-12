from .abstract import Feature
from .wyscoutEventsDefinition import *
from pymongo import MongoClient
import json
from bson.code import Code


class roleFeatures(Feature):
    """
    Given the matrix for roles, it computes, for each player and match, the role of a player

    A role matrix is a data structure where, given x and y (between 0 and 100), it contains the correspinding roles for a player having center of performance = x,y
    """
    def createFeature(self,role_matrix,collectionName='roleFeatures',param={},limit=None):


        str_centroids="function(){var w=%s; return w;}"%json.dumps(role_matrix)
        #function to get all the positions for each player in each match
        matchid_playerid_positions = Code(
			"""
			function ()
			{
				var player_names=players();


				if (this.positions.length>0 &&  this.playerId != 0)
					{
				        var playerId =  this.playerId
				        var gk = 0;
						if (playerId in player_names)
						{
						    if (player_names[playerId][1] == 'Goalkeeper' ) gk=1;
						    playerId = player_names[playerId][0];

						}
						if (gk == 0) {
						    emit({'player': playerId, 'match': this.matchId}, {'x':this.positions[0].x,'y': this.positions[0].y});
						}
						else { emit({'player': playerId, 'match': this.matchId}, {'x':-1 ,'y': -1}); }

					}

			}
			""")

        reducer_avgpos = Code("""
                function (key, values) {
                  var total_x =0;
                  var total_y = 0;
                  for (var i = 0; i < values.length; i++) {
                    total_x += values[i].x;
                    total_y += values[i].y;
                  }
                  return {'x':total_x/values.length,'y':total_y/values.length};
                }
                """)

        reducer_void=Code(""" //reducer void, should be never called
        function(key,values){
            return values[0];
        }
        """)
        #map function to return cluster associated to each average position of each player in each match
        roleAssociation= Code("""
            function() {
            	var centers=w();
                var min_dist=0;
                var cluster=-1;
                var avg_pos= [this.value.x,this.value.y]
                if ((avg_pos[0] + avg_pos[1] )!= -2) //not a goalkeeper
                {

                  var discrete_x = Math.floor(avg_pos[0]).toString();
                  var discrete_y = Math.floor(avg_pos[1]).toString();
                  cluster = centers[discrete_x][discrete_y];
                  emit ({'player':this._id.player,'match':this._id.match,'name':'cluster'},cluster)
                }
                else emit({'player':this._id.player,'match':this._id.match,'name':'cluster'},-1)

            }
        """)


        client = MongoClient('localhost', 27017)
        db = client.wyscout_playerank

        #set name of players
        players={x['wyId']:(x['shortName'],x['role']['name']) for x in
         list(db.players.find({},{'wyId':1,'shortName':1,'role':1})) if 'shortName' in x}
        players[0]='0'
        str_players="""function(){var data=%s; return data;}"""%json.dumps(players)

        #filter matches
        matches = [x['wyId'] for x in db.matches.find(param,{'wyId':1})][:limit]
        matches = [x['_id']['match'] for x in db.playerankFeatures.find()]

        ###2 step aggregation: first avgpos then role association
        roleCollection= db.events.map_reduce(matchid_playerid_positions,reducer_avgpos,collectionName,
                     query={'matchId':{'$in':matches}},scope={ 'players': Code(str_players)})
        roleCollection= roleCollection.map_reduce(roleAssociation,reducer_void,collectionName,
                     scope={"w":Code(str_centroids)})
        return roleCollection
