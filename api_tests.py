import os
import api
import unittest
import tempfile
import json
from datetime import datetime 

class ApiTestCase(unittest.TestCase):

	def setUp(self):
		"""Run before every test case"""
		self.db_fd, api.app.config['DATABASE_PATH'] = tempfile.mkstemp()
		api.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + api.app.config['DATABASE_PATH']
		api.app.config['TESTING'] = True
		self.app = api.app.test_client()
		api.init_db()

	def tearDown(self):
		"""Run after every test case"""
		os.close(self.db_fd)
		os.unlink(api.app.config['DATABASE_PATH'])

	def test_empty_db(self):
		"""Check resource responses from an empty database"""
		# Get games
		rv = self.app.get('/games')
		resp = json.loads(rv.data)
		assert len(resp) == 0
		# Get users
		resp = self.app.get('/users')
		users = json.loads(resp.data)
		assert len(users) == 0

	def test_create_user(self):
		"""Attempt to create a user"""
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '1985-04-03',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201

	def test_create_dup_user(self):
		"""Attempt to create a duplicate user"""
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '1985-04-03',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201

		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 400

	def test_update_user(self):
		"""Attempt to update an existing user"""
		# Create a user
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '1985-04-03',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201

		j = json.loads(resp.data)

		# Change user information
		j['name'] = 'bobby'
		j['first_name'] = 'Bob'
		j['last_name'] = 'Jones'
		j['birthday'] = '1988-05-26'
		j['email'] = 'bob@jones.com'

		resp = self.app.put('/users/%s' % (j['id']), content_type='application/json', data=json.dumps(j))
		assert resp.status_code == 204


	def test_delete_user(self):
		"""Attempt to delete a user"""
		# Create a user
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '1985-04-03',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201

		j = json.loads(resp.data)

		# Delete the user 
		resp = self.app.delete('/users/%s' % (j['id'],))
		assert resp.status_code == 204

	def test_multi_users(self):
		"""Attempt to create multiple users"""
		# Create users 
		user_json = json.dumps({
			'name': 'user1'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201 

		user_json = json.dumps({
			'name': 'user2'
		})
		resp = self.app.post('/users', content_type='application/json', data=user_json)
		assert resp.status_code == 201 

		# Get users 
		resp = self.app.get('/users')
		assert resp.status_code == 200 

		users = json.loads(resp.data)

		assert len(users) == 2
		assert users[0]['name'] == 'user1'
		assert users[1]['name'] == 'user2'

	def test_no_games(self):
		"""Attempt to access game resources where no games exists"""
		# Get specific game 
		resp = self.app.get('/games/1')
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

		# Get game's scores
		resp = self.app.get('/games/1/scores')
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

		# Get game's players
		resp = self.app.get('/games/1/players')
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

		# Get game's teams 
		resp = self.app.get('/games/1/teams')
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

		# Delete a game
		resp = self.app.delete('/games/1')
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

		# Add a score
		resp = self.app.post('/games/1/score', data={ 'player_id': 1 })
		assert resp.status_code == 404
		assert resp.data == 'game does not exist'

	def test_create_delete_game(self):
		"""Attempt to create a game and delete a game. Backfill users for
		   required game data"""
		
		# Create users we'll use for game 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game 
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1,
				 	  }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[3] },
				 	  'position': 4 } ]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 201

		game_json = json.loads(resp.data)

		# Delete game 
		resp = self.app.delete('/games/%s' % (game_json['id'],))
		assert resp.status_code == 204

	def test_game_bad_user(self):
		"""Create a game with bad users"""

		# Create game with nonexistent users
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': 1 },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': 2 },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': 3 },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': 4 },
				 	  'position': 4 } ]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': 5 },
				 	  'position': 1 },
				 	{ 'user': { 'id': 6 },
				 	  'position': 2 },
				 	{ 'user': { 'id': 7 },
				 	  'position': 3 },
				 	{ 'user': { 'id': 8 },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'user does not exist'

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game with same user on opposite teams
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[3] },
				 	  'position': 4 } ]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'each user can only be on a single team'

	def test_game_bad_position(self):
		"""Create a game with bad position data"""

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create a game with too many positions on a team
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'too many players on team'

		# Create a game with position less than 1
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 0 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'player must be in position 1-4'

		# Create a game with position > 4
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 5 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'player must be in position 1-4'

	def test_game_bad_teams(self):
		"""Create games with incorrectly defined teams"""

		# Add users
		user_ids = []
		for i in range(12):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Test three teams 
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'yellow',
				 	'players': [
				 	{ 'user': { 'id': user_ids[8] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[9] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[10] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[11] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 400
		assert resp.data == 'too many teams'

	def test_game_scores(self):
		"""Send score data to a created game"""

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 201

		game = json.loads(resp.data)
		player_id = game.get('teams')[0].get('players')[0].get('id')

		# Create a new score
		score_json = json.dumps({
			'player_id': player_id,
			'own_goal': False 
		})
		# Send a score to the game
		resp = self.app.post('/games/%s/score' % (game.get('id')), \
			content_type='application/json', data=score_json)
		assert resp.status_code == 201

		# Send a score with a time to the game
		score_json = json.dumps({
			'player_id': player_id, 
			'own_goal': False,
			'time': datetime.now().isoformat()
		})
		resp = self.app.post('/games/%s/score' % (game.get('id')), \
			content_type='application/json', data=score_json)
		assert resp.status_code == 201

		# Send an own goal 
		score_json = json.dumps({
			'player_id': player_id,
			'own_goal': True
		})
		resp = self.app.post('/games/%s/score' % (game.get('id')), \
			content_type='application/json', data=score_json)
		assert resp.status_code == 201 

	def test_full_score(self):
		"""Score an entire game"""

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game
		game_json = json.dumps({
			'start': datetime.now().isoformat(),
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 201

		game = json.loads(resp.data)
		player_id = game.get('teams')[0].get('players')[0].get('id')

		# Give player 10 scores
		for i in range(10):
			score_json = json.dumps({
				'player_id': player_id, 
				'own_goal': False 
			})
			resp = self.app.post('/games/%s/score' % (game.get('id')), \
				content_type='application/json', data=score_json)
			assert resp.status_code == 201

		# Try to give player another score. Verify error.
		score_json = json.dumps({
			'player_id': player_id, 
			'own_goal': False 
		})
		resp = self.app.post('/games/%s/score' % (game.get('id')),
			content_type='application/json', data=score_json)
		assert resp.status_code == 400
		assert resp.data == 'team already has 10 points'

	def test_game_put(self):
		"""Update a game's state through PUT requests"""

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game
		game_json = json.dumps({
			'start': '2015-04-02 23:33:00',
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1 }, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3 }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4 }]},
				 { 
				 	'name': 'blue',
				 	'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1 },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2 },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3 },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4 }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 201

		game = json.loads(resp.data)

		# Send PUT to update teams
		# Send PUT to update score
		game['teams'][0]['players'][0]['scores'] = [
			{
				'time': '2015-04-02 23:33:01',
				'own_goal': False
			}
		]
		game_json = json.dumps(game)

		resp = self.app.put('/games/%s' % (game['id']), content_type='application/json',\
			data=game_json)

		assert resp.status_code == 200

		game = json.loads(resp.data)

		# Send PUT to finish adding scores
		game['teams'][0]['players'][0]['scores'].extend([
			{ 'time': '2015-04-02T23:33:02'},
			{ 'time': '2015-04-02T23:33:03'}])

		game['teams'][0]['players'][1]['scores'].extend([
			{ 'time': '2015-04-02T23:33:08'},
			{ 'time': '2015-04-02T23:33:09'}])

		game['teams'][0]['players'][2]['scores'].extend([
			{ 'time': '2015-04-02T23:33:10'},
			{ 'time': '2015-04-02T23:33:11'}])

		game['teams'][0]['players'][3]['scores'].extend([
			{ 'time': '2015-04-02T23:33:16'},
			{ 'time': '2015-04-02T23:33:17'},
			{ 'time': '2015-04-02T23:33:18'}])

		game['teams'][1]['players'][0]['scores'].extend([
			{ 'time': '2015-04-02T23:33:04'},
			{ 'time': '2015-04-02T23:33:05'}])

		game['teams'][1]['players'][1]['scores'].extend([
			{ 'time': '2015-04-02T23:33:06'},
			{ 'time': '2015-04-02T23:33:07'}])

		game['teams'][1]['players'][2]['scores'].extend([
			{ 'time': '2015-04-02T23:33:12'},
			{ 'time': '2015-04-02T23:33:13'}])

		game['teams'][1]['players'][3]['scores'].extend([
			{ 'time': '2015-04-02T23:33:14'},
			{ 'time': '2015-04-02T23:33:15'}])

		game_json = json.dumps(game, indent=2)

		resp = self.app.put('/games/%s' % (game['id']), content_type='application/json',\
			data=game_json)
		assert resp.status_code == 200 

		game = json.loads(resp.data)
		# Verify game ended
		#assert game['end'] is not None

		# Send PUT to try adding scores to a completed game
		game['teams'][0]['players'][0]['scores'].append({
			'time': '2015-04-02 23:34:00',
		})

		game_json = json.dumps(game, indent=2)

		resp = self.app.put('/games/%s' % (game['id']), content_type='application/json',\
			data=game_json)
		assert resp.status_code == 400 
		assert resp.data == 'each team can have a max of 10 points'

	# Create an entire game with a single game POST.
	def test_entire_game(self):
		"""Create an entire, complete game in one POST"""

		# Add users 
		user_ids = []
		for i in range(8):
			user_json = json.dumps({
				'name': 'user%s' % (i,)
			})
			resp = self.app.post('/users', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			u = json.loads(resp.data)
			user_ids.append(u['id'])

		# Create game
		game_json = json.dumps({
			'start': '2015-05-01 18:11:10',
			'end': '2015-05-01 18:12:00',
			'teams': [
				{ 
					'name': 'red',
					'players': [
				 	{ 'user': { 'id': user_ids[0] },
				 	  'position': 1, 
				 	  'scores': [
				 	   	{ 'time': '2015-05-01T18:11:12'}, 
				 	   	{ 'time': '2015-05-01T18:11:20'}, 
				 	   	{ 'time': '2015-05-01T18:11:21',
				 	   	  'own_goal': True }]}, 
				 	{ 'user': { 'id': user_ids[1] },
				 	  'position': 2,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:13'}, 
				 	  	{ 'time': '2015-05-01T18:11:22'}]}, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 3,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:14'},
				 	  	{ 'time': '2015-05-01T18:11:23'}] }, 
				 	{ 'user': { 'id': user_ids[2] },
				 	  'position': 4,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:24'},
				 	  	{ 'time': '2015-05-01T18:11:25'}]}
				 ]
				},
				{ 
					'name': 'blue',
					'players': [
				 	{ 'user': { 'id': user_ids[4] },
				 	  'position': 1,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:16'}, 
				 	  	{ 'time': '2015-05-01T18:11:26'}] },
				 	{ 'user': { 'id': user_ids[5] },
				 	  'position': 2,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:17'}, 
				 	  	{ 'time': '2015-05-01T18:11:27'}, 
				 	  	{ 'time': '2015-05-01T18:11:28'}] },
				 	{ 'user': { 'id': user_ids[6] },
				 	  'position': 3,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:18'}, 
				 	  	{ 'time': '2015-05-01T18:11:29'}] },
				 	{ 'user': { 'id': user_ids[7] },
				 	  'position': 4,
				 	  'scores': [
				 	  	{ 'time': '2015-05-01T18:11:19'}, 
				 	  	{ 'time': '2015-05-01T18:11:30'}] }]}
				 ]
		})
		resp = self.app.post('/games', content_type='application/json', data=game_json)
		assert resp.status_code == 201


if __name__ == '__main__':
	unittest.main()