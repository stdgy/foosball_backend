
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