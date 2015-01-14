import os
from datetime import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
        render_template, flash, jsonify, make_response
from flask.ext.sqlalchemy import SQLAlchemy
from foosball_models import User, Game, Team, Player, Score 

# create our application
app = Flask(__name__)

app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://danny@localhost/testdb',
    DEBUG=True
))

db = SQLAlchemy(app)

# Routes
@app.route('/games', methods=['GET'])
def get_games():
    games = db.session.query(Game)

    # Check whether any filters were passed in.
    # Allowed filters:
    #    User
    #    Time Range - start, end
    #    

    if 'user_id' in request.values:
        uid = request.values['user_id']
        games = games.filter(Game.players.any(user_id=uid))

    return jsonify( games=[game.serialize for game in games])

@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User)
    return jsonify( users=[user.serialize for user in users])

@app.route('/user', methods=['POST'])
def create_user():
    u_json = request.json 
    user = User()

    if 'name' in u_json:
        user.name = u_json['name']
    else:
        return abort(400)
    
    if 'first_name' in u_json:
        user.first_name = u_json['first_name']

    if 'last_name' in u_json:
        user.last_name = u_json['last_name']

    if 'birthday' in u_json:
        try:
            user.birthday = datetime.strptime(u_json['birthday'],\
                                '%m/%d/%Y')
        except ValueError:
            return abort(400)

    if 'email' in u_json:
        user.email = u_json['email']

    db.session.add(user)
    db.session.commit()

    return make_response('', '201', { 'location': '/users/%s' % (user.id) })

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
        return abort(405)

    user = users.first()
    db.session.delete(user)
    db.session.commit()

    return make_response(('', 200, ''))

@app.route('/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    # check count
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return abort(404)

    game = db.session.query(Game).filter(Game.id == game_id).first()

    g = {
        'id': game.id,
        'start': game.start,
        'end': game.end,
        'teams': [],
        'scores': []
    }

    for team in game.teams:
        t = {
            'id': team.id,
            'players': []
        }
        for player in team.players:
            t['players'].append({
                'id': player.id,
                'position': player.position,
                'name': player.user.name
            })
        g['teams'].append(t)

    for score in game.scores:
        g['scores'].append({
            'id': score.id,
            'player_id': score.player_id,
            'team_id': score.team_id
        })

    return jsonify( g )

@app.route('/games/<int:game_id>/players', methods=['GET'])
def get_players(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return abort(404)

    players = db.session.query(Player).filter(Game.id == game_id)\
            .filter(Game.id == Player.game_id)\
            .order_by(Player.team_id, Player.position)

    return jsonify( players=[ player.serialize for player in players ])

@app.route('/games/<int:game_id>/scores', methods=['GET'])
def get_scores(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return abort(404)

    scores = db.session.query(Score).filter(Game.id == game_id)\
            .filter(Game.id == Score.game_id)\
            .order_by(Score.id)

    return jsonify( scores=[ score.serialize for score in scores ])

@app.route('/games/<int:game_id>/score', methods=['POST'])
def make_score(game_id):
    # Try to get form keys 
    player_id = request.form['player_id']

    if player_id == None:
        return abort(404)

    player = db.session.query(Player)\
            .filter(Player.id == player_id).first()

    score = Score(player_id=player.id, team_id=player.team_id,\
                game_id=player.game_id)

    db.session.add(score)
    db.session.commit()

    return make_response(('', 201, \
        { 'location': 'games/' + str(player.game_id) + '/scores/' + str(score.id) }))

@app.route('/games/<int:game_id>/teams', methods=['GET'])
def get_teams(game_id):
    # Sanity check
    count = db.session.query(Game).filter(Game.id == game_id).count()

    if count == 0:
        return abort(404)

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
            return abort(404)

    db.session.add(g)
    db.session.commit()

    # Create teams 
    if 'teams' in g_json:
        for team in g_json['teams']:
            t = Team()
            t.game_id = g.id
            if 'players' in team:
                for player in team['players']:
                    p = Player()
                    p.position = player['position']
                    p.user_id = player['user_id']
                    p.game_id = t.game_id 
                    t.players.append(p)
            g.teams.append(t)

    db.session.commit()

    return make_response(('', 201, \
        { 'location': 'games/%s' % (g.id) }))

# Delete a game
@app.route('/game/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    games = db.session.query(Game)\
            .filter(Game.id == game_id)

    if games.count() != 1:
        return abort(404)

    g = games.first()

    db.session.delete(g)
    db.session.commit()

    return make_response(('', 200, None))


@app.route("/static/<path:path>", methods=['GET'])
def serve_static(path):
    return app.send_static_file(os.path.join('static', path))

if __name__ == '__main__':
    app.run(host='127.0.0.1')
