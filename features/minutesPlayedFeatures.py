from .abstract import Feature
from wyscoutEventsDefinition import *
from pymongo import MongoClient
import json
from bson.code import Code


class minutesPlayedFeatures(Feature):
    """
    It computes, for each player and match, the total time (in minutes) played
    """
    def createFeature(self,collectionName='minutesPlayedFeatures',param={},limit=None):

        """
        using matches collection to compute minutes played

        output: a collection of documents in the format
        {'match': <int>, 'player' : <int>, 'name': <str>},value
        """

        match_player_minutes= Code("""
        function()
        { // map function to get minutes for each player

            var duration = 90;
            if (this.duration != 'Regular') duration = 120; // extended time

            var teams = Object.keys(this.teamsData);
            var player_names=players();
            var team_names=teamName()

            for (var i = 0; i<teams.length ; i++ )
            {
				var team= teams[i]
                var minutesPlayed = {};
                var goals_scored = {};
                var teamData = this.teamsData[team];
                if ('substitutions' in teamData.formation && teamData.formation.substitutions.constructor === Array)
                {
                     teamData.formation.substitutions.forEach(function (s){
                     var minute= s.minute;

                     var playerId = s.playerOut; //exiting player
                    if (playerId in player_names) playerId = player_names[playerId];

                     minutesPlayed[playerId] = minute;

                     playerId=s.playerIn;
                     if (playerId in player_names) playerId = player_names[playerId];

                     minutesPlayed[playerId] = duration - minute;


                     });
                }

                if ('lineup' in teamData.formation && teamData.formation.lineup.constructor === Array)
                {
            	   this.teamsData[team].formation.lineup.forEach(function (p){
            	   var playerId = p.playerId;
            	   var goals= p.goals;
                   if (playerId in player_names) playerId = player_names[playerId];

                   // check: player not substituted
                   if (!(playerId in minutesPlayed))  minutesPlayed[playerId] = duration;

                   if (!(isNaN(goals))) goals_scored[playerId] = goals;
                   else goals_scored[playerId] = 0;

            	 });
            	}
            	if ('bench' in teamData.formation && teamData.formation.bench.constructor === Array)
                {
             	  this.teamsData[team].formation.bench.forEach(function (p){
            	   var playerId = p.playerId;
            	   var goals= p.goals;
                   if (playerId in player_names) playerId = player_names[playerId];

                   if (!(isNaN(goals))) goals_scored[playerId] = goals;
                   else goals_scored[playerId] = 0;

            	 });
            	}
            	//emitting players minute

            	player_all = Object.keys(minutesPlayed);
            	for (var j = 0; j < player_all.length; j++)
            	{
            	    var player = player_all[j];
            		emit({'match': this.wyId, 'player' : player, 'name': 'minutesPlayed'},minutesPlayed[player]);
            		emit({'match': this.wyId, 'player' : player, 'name': 'teamName'}, team_names[team]);
            		emit({'match': this.wyId, 'player' : player, 'name': 'timestamp'},this.dateutc);
            		emit({'match': this.wyId, 'player' : player, 'name': 'goalScored'},goals_scored[player])
            	}

            }
        }
        """)

        reducer_void=Code(""" //reducer void, should be never called
        function(key,values){
            return values[0];
        }
        """)

        client = MongoClient('localhost', 27017)
        db = client.wyscout_playerank

        #set name of players
        players={x['wyId']:x['shortName'] for x in
         list(db.players.find({},{'wyId':1,'shortName':1})) if 'shortName' in x}
        players[0]='0'
        teams={x['wyId']:x['name'] for x in
         list(db.teams.find({},{'wyId':1,'name':1})) }
        teams[0]='0'

        str_players="""function(){var data=%s; return data;}"""%json.dumps(players)
        str_teams="""function(){var data=%s; return data;}"""%json.dumps(teams)

        #filter matches
        players_tofetch = json.load(open('players_seriea2018.json'))
        matches = [x['wyId'] for x in db.matches.find(param,{'wyId':1})][:limit]
        matches = [x['_id']['match'] for x in db.playerankFeatures.find()]

        query={'wyId':{'$in': matches}}
        print db.matches.find(query).count()

        minutesCollection= db.matches.map_reduce(match_player_minutes,reducer_void,collectionName,
                     query=query,scope={ 'players': Code(str_players), 'teamName' : Code(str_teams)})

        return minutesCollection
