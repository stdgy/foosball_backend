from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref 
from flask.ext.sqlalchemy import SQLAlchemy

#Base = declarative_base()
db = SQLAlchemy()

class User(db.Model):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False, unique=True)
	first_name = Column(String)
	last_name = Column(String)
	birthday = Column(Date)
	email = Column(String)

	players = relationship("Player", backref="user")

	@property 
	def serialize(self):
		"""Return User Object"""
		return {
			'id': self.id,
			'name': self.name,
			'first_name': self.first_name,
			'last_name': self.last_name,
			'birthday': self.birthday.strftime('%m/%d/%Y') if self.birthday is not None\
					else '',
			'email': self.email
		}

	def __repr__(self):
		return ("<User(name='%s', first_name='%s', last_name='%s', "
			"birthday='%s', email='%s')>") % (self.name, self.first_name, 
			self.last_name, self.birthday, self.email)

class Game(db.Model):
	__tablename__ = 'games'
	id = Column(Integer, primary_key=True)
	start = Column(DateTime)
	end = Column(DateTime)

	players = relationship("Player", backref="game",
				cascade="all, delete, delete-orphan")
	teams = relationship("Team", backref="game",
				cascade="all, delete, delete-orphan")
	scores = relationship("Score", backref="game",
				cascade="all, delete, delete-orphan")

	@property 
	def serialize(self):
		teams = []
		for team in self.teams:
			t = { 
				'id': team.id,
				'players': [] 
			}
			for player in team.players:
				t['players'].append({
					'id': player.id,
					'position': player.position,
					'user': player.user.serialize
				})
			teams.append(t)

		"""Return full Game object"""
		return {
			'id': self.id,
			'start': self.start.strftime('%m/%d/%Y %H:%M:%S') if self.start is not None\
					else '',
			'end': self.end.strftime('%m/%d/%Y %H:%M:%S') if self.end is not None\
					else '',
			'teams': teams
		}

	@property 
	def serialize_players(self):
		return [ player.serialize for player in self.players ]

	@property 
	def serialize_teams(self):
		return [ team.serialize for team in self.teams ]

	@property 
	def serialize_scores(self):
		return [ score.serialize for score in self.scores ]

	def __repr__(self):
		return "<Game(start='%s', end='%s')>" % (self.start, self.end)

class Team(db.Model):
	__tablename__ = 'teams'
	id = Column(Integer, primary_key=True)
	game_id = Column(Integer, ForeignKey('games.id'))

	players = relationship("Player", backref="team")

	@property 
	def serialize(self):
		"""Return Team object"""
		return {
			'id': self.id,
			'game_id': self.game_id
		}

	def __repr__(self):
		return "<Team(game_id='%s')>" % self.game_id

class Player(db.Model):
	__tablename__ = 'players'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	game_id = Column(Integer, ForeignKey('games.id'))
	team_id = Column(Integer, ForeignKey('teams.id'))
	position = Column(Integer)

	scores = relationship("Score", backref="player")

	@property 
	def serialize(self):
		"""Return Player object"""
		return {
			'id': self.id,
			'user_id': self.user_id,
			'game_id': self.game_id,
			'team_id': self.team_id,
			'position': self.position
		}

	def __repr__(self):
		return ("<Player(user_id='%s', game_id='%s', team_id='%s', "
			"position='%s')>") % (self.user_id, self.game_id, self.team_id, self.position)

class Score(db.Model):
	__tablename__ = 'scores'
	id = Column(Integer, primary_key=True)
	player_id = Column(Integer, ForeignKey('players.id'))
	game_id = Column(Integer, ForeignKey('games.id'))
	team_id = Column(Integer, ForeignKey('teams.id'))
	time = Column(DateTime)
	own_goal = Column(Boolean)

	@property 
	def serialize(self):
		"""Return Score Object"""
		return {
			'id': self.id,
			'player_id': self.player_id,
			'game_id': self.game_id,
			'team_id': self.team_id
		}

	def __repr__(self):
		return ("<Score(player_id='%s', game_id='%s', team_id='%s', "
			"own_goal='%s')>") % (self.player_id, self.game_id, self.team_id, self.own_goal)