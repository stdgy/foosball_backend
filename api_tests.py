import os
import api
import unittest
import tempfile
import json

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
		assert len(resp['games']) == 0
		# Get users
		resp = self.app.get('/users')
		users = json.loads(resp.data)
		assert len(users['users']) == 0

	def test_create_user(self):
		"""Attempt to create a user"""
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '03/04/1985',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 201

	def test_create_dup_user(self):
		"""Attempt to create a duplicate user"""
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '03/04/1985',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 201

		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 400

	def test_delete_user(self):
		"""Attempt to delete a user"""
		# Create a user
		user_json = json.dumps({
			'name': 'danny', 
			'first_name': 'Danny', 
			'last_name': 'Boy',
			'birthday': '03/04/1985',
			'email': 'test@fake.com'
		})
		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 201

		j = json.loads(resp.data)

		# Delete the user 
		resp = self.app.delete('/user/%s' % (j['id'],))
		assert resp.status_code == 200

	def test_multi_users(self):
		"""Attempt to create multiple users"""
		# Create users 
		user_json = json.dumps({
			'name': 'user1'
		})
		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 201 

		user_json = json.dumps({
			'name': 'user2'
		})
		resp = self.app.post('/user', content_type='application/json', data=user_json)
		assert resp.status_code == 201 

		# Get users 
		resp = self.app.get('/users')
		assert resp.status_code == 200 

		users = json.loads(resp.data)

		assert len(users['users']) == 2
		assert users['users'][0]['name'] == 'user1'
		assert users['users'][1]['name'] == 'user2'

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
			resp = self.app.post('/user', content_type='application/json', data=user_json)
			assert resp.status_code == 201 
			user_ids.append(resp.data)

		# Create game 
	

if __name__ == '__main__':
	unittest.main()