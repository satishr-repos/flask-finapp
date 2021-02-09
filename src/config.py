
"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

TESTING = True
DEBUG = True
FLASK_ENV = 'development'
SECRET_KEY = environ.get('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = environ.get('USER_DATABASE')
SQLALCHEMY_TRACK_MODIFICATIONS = False
DOWNLOADS_PATH = path.join(basedir, environ.get('DOWNLOADS_PATH'))
