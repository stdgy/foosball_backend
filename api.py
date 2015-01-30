import os
from datetime import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
        render_template, flash, jsonify, make_response
from models import User, Game, Team, Player, Score
from models import db 

# create our application
app = Flask(__name__)

app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://danny@localhost/testdb',
    DEBUG=True
))


db.init_app(app)

def init_db():
    db.app = app 
    #db.init_app(app)
    # Create tables 
    db.create_all()

# Routes
@app.route('/games', methods=['GET'])
def get_games():
    games = db.session.query(Game)

    # Check whether any filters were passed in.
    # Allowed filters:
    #    user_id -- Games that contain players with user_id
    #    started_before -- Games that started before [time] exclusive
    #    started_after -- Games that started after [time] inclusive
    if 'user_id' in request.values:
        uid = request.values['user_id']
        try:
            uid = int(uid)
        except ValueError:
            return make_response('User_id must be an integer.', '400',\
                '')
        games = games.filter(Game.players.any(user_id=uid))

    if 'started_after' in request.values:
        after = request.values['started_after']
        try:
            after = datetime.strptime(after,\
                    '%m/%d/%Y')
        except ValueError:
            return make_response('Bad date format. Should be mm/dd/yyyy.', '400',\
                '')

        games = games.filter(Game.start >= after)

    if 'started_before' in request.values:
        before = request.values['started_before']
        try:
            before = datetime.strptime(before,\
                    '%m/%d/%Y')
        except ValueError:
            return make_response('Bad date format. Should be mm/dd/yyyy.', '400',\
                '')

        games = games.filter(Game.start < before)
    
    return jsonify( games=[game.serialize for game in games])

@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User)
    return jsonify( users=[user.serialize for user in users])

@app.route('/user', methods=['POST'])
def create_user():
    u_json = request.json 
    u = User()

    if 'name' in u_json:
        u.name = u_json['name']
    else:
        return abort(400)

    if u.name == '':
        return make_response('must include a name', '400', '')

    if db.session.query(User).filter(User.name == u.name).count() > 0:
        return make_response('user already exists', '400', '')
    
    if 'first_name' in u_json:
        u.first_name = u_json['first_name']

    if 'last_name' in u_json:
        u.last_name = u_json['last_name']

    if 'birthday' in u_json:
        try:
            u.birthday = datetime.strptime(u_json['birthday'],\
                                '%m/%d/%Y')
        except ValueError:
            return make_response('birthday must be in format: mm/dd/yyyy', '400',\
                '')

    if 'email' in u_json:
        u.email = u_json['email']

    db.session.add(u)
    db.session.commit()

    resp = jsonify(u.serialize)
    resp.status_code = 201

    return resp

@app.route('/users/<int:user_id>', methods=['PUT'])
def put_user(user_id):
    """Update an existng user object"""
    # Check that user exists 
    user = db.session.query(User).filter(User.id == user_id)

    if user.count() == 0:
        return make_response('user does not exist', '404', '')

    user = user.first()
    user_json = request.json

    # Update non-key fields for user
    user.name = user_json.get('name', user.name)
    user.first_name = user_json.get('first_name', user.first_name)
    user.last_name = user_json.get('last_name', user.last_name)
    if 'birthday' in user_json:
        try:
            user.birthday = datetime.strptime(user_json.get('birthday'),\
                '%m/%d/%Y')
        except ValueError:
            return make_response('birthday must be in form mm/dd/yyyy', '400', '')
    user.email = user_json.get('email', user.email)

    db.session.commit()

    j_response = jsonify(user.serialize)
    j_response.status_code = 204

    return j_response

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    users = db.session.query(User)\
            .filter(User.id == user_id)

    if users.count() != 1:
        return abort(404)

    # Check if the user is in any games. If so, don't allow delete
    player_count = db.session.query(Player)\
                .filter(Player.user_id == user_id)\
                .count()

    if player_count > 0:
        return make_response("can't delete user that is in games", '405', '')

    user = users.first()
    db.session.delete(user)
    db.session.commit()

    return make_response('', 204, '')

@app.route('/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    # check count
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return make_response('game does not exist', '404', '')

    game = db.session.query(Game).filter(Game.id == game_id).first()

    return jsonify( g.serialize )

@app.route('/games/<int:game_id>/players', methods=['GET'])
def get_players(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return make_response('game does not exist', '404', '')

    players = db.session.query(Player).filter(Game.id == game_id)\
            .filter(Game.id == Player.game_id)\
            .order_by(Player.team_id, Player.position)

    return jsonify( players=[ player.serialize for player in players ])

@app.route('/games/<int:game_id>/scores', methods=['GET'])
def get_scores(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return make_response('game does not exist', '404', '')

    scores = db.session.query(Score).filter(Game.id == game_id)\
            .filter(Game.id == Score.game_id)\
            .order_by(Score.id)

    return jsonify( scores=[ score.serialize for score in scores ])

@app.route('/games/<int:game_id>/score', methods=['POST'])
def make_score(game_id):
    """Takes a JSON object representing a new score and inserts it into the db"""
    # Check that game exists 
    game = db.session.query(Game).filter(Game.id == game_id)

    if game.count() == 0:
        return make_response('game does not exist', '404', '')

    # Check that game isn't over 
    game = game.first()
    if game.end is not None:
        return make_response('game is already over', '400', '')

    # Check that neither team already has 10 points in game
    for team in game.teams:
        total_score = 0
        for player in team.players:
            for score in player.scores:
                if score.own_goal:
                    total_score -= 1
                else:
                    total_score += 1
        if total_score >= 10:
            return make_response('team already has 10 points', '400', '')

    # Make sure JSON was passed in
    if request.json is None:
        return make_response('must pass in score object', '400', '')

    # Load json
    score_json = request.json
    player_id = score_json.get('player_id')
    time = score_json.get('time')
    own_goal = score_json.get('own_goal')

    if player_id is None:
        return make_response('must pass player_id', 400, '')

    # See if time scored was sent in. If not, populate.
    if time is None:
        time = datetime.now()
    else:
        try:
            time = datetime.strptime(time, '%m/%d/%Y %H:%M:%S')
        except ValueError:
            return make_response('time must be encoded mm/dd/yyyy hh:mm:ss',\
                '400', '')

    # Check own goal. If not sent in, set to false.
    if own_goal is None:
        own_goal = False

    player = db.session.query(Player)\
            .filter(Player.id == player_id)\
            .filter(Player.game_id == game_id)

    # Check that player exists 
    if player.count() != 1:
        return make_response('player not found', '404', '')

    player = player.first()

    score = Score(player_id=player.id, team_id=player.team_id,\
                game_id=player.game_id, time=time, own_goal=own_goal)

    db.session.add(score)
    db.session.commit()

    r_json = jsonify(score.serialize)
    r_json.status_code = 201 

    return r_json 

@app.route('/games/<int:game_id>/teams', methods=['GET'])
def get_teams(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return make_response('game does not exist', '404', '')

    teams = db.session.query(Team).filter(Game.id == game_id)\
            .filter(Game.id == Team.game_id)\
            .order_by(Team.id)

    results = []

    for team in teams:
        t = {}
        t['id'] = team.id
        t['players'] = []

        for player in team.players:
            t['players'].append({
                "id": player.id,
                "position": player.position,
                "name": player.user.name
                })

        results.append(t)

    return jsonify( teams=results )

# Create a game
@app.route('/game', methods=['POST'])
def create_game():
    # Game is sent in as JSON
    g_json = request.json
    
    g = Game()

    if 'start' not in g_json:
        g.start = datetime.now()
    else:
        try:
            g.start = datetime.strptime(g_json['start'], '%m/%d/%Y %H:%M:%S')
        except ValueError:
            return make_response('start must be in format: mm/dd/yyyy hh:mi:ss',\
                '400', '')

    # Create teams 
    if 'teams' in g_json:
        # Make sure there are two teams 
        if len(g_json['teams']) != 2:
            return make_response('must provide two teams for a game', '400', '')
        for team in g_json['teams']:
            t = Team()
            g.teams.append(t)
            if 'players' in team:
                # Make sure four players supplied
                if len(team['players']) != 4:
                    return make_response('must provide 4 players to a team', '400', '')
                for player in team['players']:
                    p = Player()

                    try:
                        p.position = int(player['position']) 
                    except ValueError:
                        return make_response('position must be an integer', '400',\
                            '')
                    try:
                        p.user_id = int(player['user_id'])
                    except ValueError:
                        return make_response('user_id must be an integer', '400',\
                            '')

                    # Check that user exists 
                    if db.session.query(User).filter(User.id == p.user_id).count() \
                    != 1:
                        return make_response('user_id must reference existing user',\
                            '400', '')

                    # Check that position is valid: 1-4
                    if p.position < 1 or p.position > 4:
                        return make_response('position must be 1 - 4', '400'\
                            '')

                    # Check that player isn't already in position
                    if len([player for p2 in t.players if p2.position == p.position]) > 0:
                        return make_response('only one player per position per team', '400',\
                            '')

                    g.players.append(p)
                    t.players.append(p)

                    # Read in any scores for player 
                    if 'scores' in player:
                        for score in player.get('scores'):
                            s = Score() 
                            # Time must be in score 
                            if 'time' in score:
                                try:
                                    s.time = datetime.strptime(score.get('time'), '%m/%d/%Y %H:%M:%S')
                                except ValueError:
                                    make_response('score time must be in mm/dd/yyyy hh:mi:ss',\
                                        '400', '')
                            else:
                                make_response('must include with a score', '400', '')

                            if 'own_goal' in score and score.get('own_goal') is True:
                                s.own_goal = True 
                            else:
                                s.own_goal = False 

                            p.scores.append(s)
                            g.scores.append(s)

            else:
                # No players supplied for team
                return make_response('must supply players for each team', '400', '')
    else:
        # No teams supplied for game 
        return make_response('must supply teams for a game', '400', '')

    # Check that the users in the first team aren't in the second team
    for player in g.teams[0].players:
        for other_player in g.teams[1].players:
            if player.user_id == other_player.user_id:
                return make_response("the same user can't be on opposing teams", '400', '')

    # See if game end time is passed in
    if 'end' in g_json:
        try:
            g.end = datetime.strptime(g_json.get('end'), '%m/%d/%Y %H:%M:%S')
        except ValueError:
            return make_response('end must be in format: mm/dd/yyyy hh:mi:ss',\
                '400', '')
        # Verify enough points passed in for game to be over 
        team1_scores = reduce(lambda x, y: x + y, map(lambda x: x.scores, g.teams[0].players))
        team2_scores = reduce(lambda x, y: x + y, map(lambda x: x.scores, g.teams[1].players))
        team1_points = len(filter(lambda x: x.own_goal is False, team1_scores)) +\
                        len(filter(lambda x: x.own_goal is True, team2_scores))
        team2_points = len(filter(lambda x: x.own_goal is False, team2_scores)) +\
                        len(filter(lambda x: x.own_goal is True, team1_scores))
        if team1_points != 10 and team2_points != 10:
            return make_response('at least one team must have 10 points for game to end',\
                '400', '')

    db.session.add(g)
    db.session.commit()

    resp = jsonify(g.serialize)
    resp.status_code = 201

    return resp

# Delete a game
@app.route('/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    games = db.session.query(Game)\
            .filter(Game.id == game_id)

    if games.count() != 1:
        return make_response('game does not exist', '404', '')

    g = games.first()

    db.session.delete(g)
    db.session.commit()

    return make_response('', 204, None)


@app.route("/static/<path:path>", methods=['GET'])
def serve_static(path):
    return app.send_static_file(os.path.join('static', path))

if __name__ == '__main__':
    app.run(host='127.0.0.1')
