import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


class AppConfig:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(AppConfig)
    return flask_app


db = SQLAlchemy()
app = create_app()

db.init_app(app)
