import os
from datetime import datetime
from dateutil.parser import parse
from flask import Flask, request, session, g, redirect, url_for, abort, \
        render_template, flash, jsonify, make_response, json
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
    #db.drop_all()
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
    #    page -- Page of results to retrieve.
    #    per_page -- Number of results per page.
    #    sort_by -- Field to sort by.
    #    order -- -1: ascending, 1: descending
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
            after = parse(after)
        except ValueError:
            return make_response('Bad date format. Should be YYYY-MM-DDThh:mm:ss.', '400',\
                '')

        games = games.filter(Game.start >= after)

    if 'started_before' in request.values:
        before = request.values['started_before']
        try:
            before = parse(before)
        except ValueError:
            return make_response('Bad date format. Should be YYYY-MM-DDThh:mm:ss.', '400',\
                '')

        games = games.filter(Game.start < before)
    
    return jsonify( games=[game.serialize for game in games])

@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User)
    return json.dumps([user.serialize for user in users])
    return jsonify( users=[user.serialize for user in users])

@app.route('/users', methods=['POST'])
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

    if u_json.get('birthday') is not None:
        try:
            u.birthday = parse(u_json['birthday'])
        except ValueError:
            return make_response('birthday must be in format: YYYY-MM-DDThh:mm:ss', '400',\
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
            user.birthday = parse(user_json.get('birthday'))
        except ValueError:
            return make_response('birthday must be in form YYYY-MM-DDThh:mm:ss', '400', '')
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
            time = parse(time)
        except ValueError:
            return make_response('time must be encoded YYYY-MM-DDThh:mm:ss',\
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
@app.route('/games', methods=['POST'])
def create_game():
    # Game is sent in as JSON
    game = request.json
    
    g = Game()

    if 'start' not in game:
        g.start = datetime.now()
    else:
        try:
            g.start = parse(game.get('start'))
        except ValueError:
            return make_response('times must be in YYYY-MM-DDThh:mm:ss',\
                '400', '')

    if game.get('end') is not None:
        try:
            g.end = parse(game.get('end'))
        except ValueError:
            make_response('times must be in YYYY-MM-DDThh:mm:ss', '400', '')

    # Iterate through passed in structures. Update/Add as needed.
    if 'teams' in game:
        for team in game['teams']:
            # New team.
            t = Team()
            g.teams.append(t)
            
            # Set values 
            t.name = team.get('name')

            if 'players' in team:
                for player in team['players']:
                    # New player.
                    p = Player()
                    g.players.append(p)
                    t.players.append(p)
                    
                    # Set values
                    p.position = player.get('position')
                    u = player.get('user')
                    if u is None or u.get('id') is None:
                        return make_response('user does not exist', '400', '')
                    p.user_id = u.get('id')

                    if 'scores' in player:
                        for score in player['scores']:
                            # New score. 
                            s = Score()
                            g.scores.append(s)
                            t.scores.append(s)
                            p.scores.append(s)
                            
                            # Set values 
                            try:
                                s.time = parse(score.get('time'))
                            except ValueError:
                                make_response('times must be in YYYY-MM-DDThh:mm:ss', '400', '')
                            s.own_goal = score.get('own_goal', False)

    # Verify that resulting game is valid
    valid_results = validate_game(g)

    # If not valid, return the error
    if (valid_results[0] is False):
        return make_response(valid_results[1], '400', '')

    db.session.add(g)
    db.session.commit()

    resp = jsonify(g.serialize)
    resp.status_code = 201

    return resp

@app.route('/games/<int:game_id>', methods=['PUT'])
def update_game(game_id):
    # Get existing game.
    g = db.session.query(Game).filter(Game.id == game_id).first()   

    # Get passed in game object 
    game = request.json 

    if g is None:
        return make_response('game does not exist', '404', '')

    if game.get('start') is not None:
        try:
            g.start = parse(game.get('start'))
        except ValueError:
            make_response('times must be in YYYY-MM-DDThh:mm:ss', '400', '')

    if game.get('end') is not None:
        try:
            g.end = parse(game.get('end'))
        except ValueError:
            make_response('times must be in YYYY-MM-DDThh:mm:ss', '400', '')

    # Iterate through passed in structures. Update/Add as needed.
    if 'teams' in game:
        for team in game['teams']:
            t = None
            if team.get('id') is None:
                # New team.
                t = Team()
                g.teams.append(t)
            else:
                # Existing team.
                t = db.session.query(Team).filter(Team.id == team.get('id'))\
                    .filter(Team.game_id == g.id).first()
                if t is None:
                    return make_response('team does not exist', '404', '')
            # Set values 
            t.name = team.get('name')

            if 'players' in team:
                for player in team['players']:
                    p = None
                    if player.get('id') is None:
                        # New player.
                        p = Player()
                        g.players.append(p)
                        t.players.append(p)
                    else:
                        # Existing player.
                        p = db.session.query(Player).filter(Player.id == player.get('id'))\
                            .filter(Player.team_id == t.id)\
                            .filter(Player.game_id == g.id).first()
                        if p is None:
                            return make_response('player does not exist', '404', '')
                    # Set values
                    p.position = player.get('position')
                    u = player.get('user')
                    if u is None or u.get('id') is None:
                        return make_response('user does not exist', '400', '')
                    p.user_id = u.get('id')

                    if 'scores' in player:
                        for score in player['scores']:
                            s = None
                            if score.get('id') is None:
                                # New score. 
                                s = Score()
                                g.scores.append(s)
                                t.scores.append(s)
                                p.scores.append(s)
                            else: 
                                # Existing score.
                                s = db.session.query(Score).filter(Score.id == score.get('id'))\
                                    .filter(Score.player_id == p.id)\
                                    .filter(Score.team_id == t.id)\
                                    .filter(Score.game_id == g.id).first()
                                if s is None:
                                    return make_response('score does not exist', '404', '')
                            # Set values 
                            try:
                                s.time = parse(score.get('time'))
                            except ValueError:
                                make_response('times must be in YYYY-MM-DDThh:mm:ss', '400', '')
                            s.own_goal = score.get('own_goal', False)

    # Verify that resulting game is valid
    valid_results = validate_game(g)

    # If not valid, return the error
    if (valid_results[0] is False):
        return make_response(valid_results[1], '400', '')

    db.session.commit()
    resp = jsonify(g.serialize)
    resp.status_code = 200
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

def can_team_score(team):
    """Check whether a team is allowed to score again"""
    # Check that team doesn't already have 10 points
    teams = team.game.teams 

    curr_score = len(filter(lambda x: x.own_goal is False, team.scores))

    if len(teams) == 2:
        other_team = None
        if teams[0].id == team.id:
            other_team = teams[1]
        else:
            other_team = teams[0]
        curr_score += len(filter(lambda x: x.own_goal is True, other_team.scores))

    if curr_score >= 10:
        return False 

    return True

def validate_game(game):
    if len(game.teams) > 2:
        return (False, 'too many teams')

    total_scores = [0, 0]

    for team in game.teams:
        if len(team.players) > 4:
            return (False, 'too many players on team')

        if len(filter(lambda x: x.name == team.name, game.teams)) > 1:
            return (False, 'each team must have a different name')

        # Use this to keep track of the total scores... Kind of stupid and ugly.
        team_index = game.teams.index(team)

        position_counts = { 1: 0, 2: 0, 3: 0, 4: 0 }
        for player in team.players:
            user_count = db.session.query(User).filter(User.id == player.user_id).count()
            if user_count == 0:
                return (False, 'user does not exist')
            if player.position is None or player.position < 1 or player.position > 4:
                return (False, 'player must be in position 1-4')
            position_counts[player.position] = position_counts[player.position] + 1 

            for score in player.scores:
                if score.own_goal is False:
                    total_scores[team_index] = total_scores[team_index] + 1 
                else:
                    total_scores[team_index-1] = total_scores[team_index-1] + 1 

        for key, val in position_counts.iteritems():
            if val > 1:
                return (False, 'more than one player in the same position')

    if None in [score.time for score in game.scores]:
        return (False, 'every score must have a time')

    if total_scores[0] > 10 or total_scores[1] > 10:
        return (False, 'each team can have a max of 10 points')

    # Verify that same user isn't on each team
    if len(game.teams) == 2:
        team1_users = set()
        for player in game.teams[0].players:
            team1_users.add(player.user_id)
        for player in game.teams[1].players:
            if player.user_id in team1_users:
                return (False, 'each user can only be on a single team')

    return (True, None)


def is_game_over(game):
    """Check whether a game is over."""
    # Check if end is set 
    if game.end is not None:
        return True 

    # Check whether either team has 10 scores
    if len(game.teams) == 2:
        team1_scores = len(filter(lambda x: x.own_goal is False, game.teams[0].scores)) +\
            len(filter(lambda x: x.own_goal is True, game.teams[1].scores))
        team2_scores = len(filter(lambda x: x.own_goal is False, game.teams[1].scores)) +\
            len(filter(lambda x: x.own_goal is True, game.teams[0].scores))

        if team1_scores == 10 or team2_scores == 10:
            return True 

    return False

if __name__ == '__main__':
    app.run(host='127.0.0.1')
