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
    return jsonify( games=[game.serialize for game in games])

@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User)
    return jsonify( users=[user.serialize for user in users])

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
@app.route('/games', methods=['POST'])
def create_game():
    # Game is sent in as JSON
    g_json = request.json
    
    g = Game()

    if g_json.start == None:
        g.start = datetime.now()
    else:
        try:
            g.start = datetime.strptime(g_json.start, '%m/%d/%Y %H:%M:%S')
        except ValueError:
            abort(404)





@app.route("/static/<path:path>", methods=['GET'])
def serve_static(path):
    return app.send_static_file(os.path.join('static', path))

if __name__ == '__main__':
    app.run(host='127.0.0.1')
