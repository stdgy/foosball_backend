from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref 

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String)
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
			'birthday': self.birthday,
			'email': self.email
		}

	def __repr__(self):
		return ("<User(name='%s', first_name='%s', last_name='%s', "
			"birthday='%s', email='%s')>") % (self.name, self.first_name, 
			self.last_name, self.birthday, self.email)

class Game(Base):
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
		"""Return full Game object"""
		return {
			'id': self.id,
			'start': self.start,
			'end': self.end,
			'players': self.serialize_players,
			'teams': self.serialize_teams,
			'scores': self.serialize_scores
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

class Team(Base):
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

class Player(Base):
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

class Score(Base):
	__tablename__ = 'scores'
	id = Column(Integer, primary_key=True)
	player_id = Column(Integer, ForeignKey('players.id'))
	game_id = Column(Integer, ForeignKey('games.id'))
	team_id = Column(Integer, ForeignKey('teams.id'))

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
			"position='%s')>") % (self.player_id, self.game_id, self.team_id, self.position)