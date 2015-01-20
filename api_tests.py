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
		rv = self.app.get('/games')
		resp = json.loads(rv.data)
		assert len(resp['games']) == 0

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

if __name__ == '__main__':
	unittest.main()