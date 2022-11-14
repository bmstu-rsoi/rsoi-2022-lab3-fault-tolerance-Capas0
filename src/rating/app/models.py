from sqlalchemy import Column, Integer, String, CheckConstraint

from .base import db, app


class Rating(db.Model):
    __tablename__ = 'rating'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    stars = Column(Integer, CheckConstraint('stars BETWEEN 0 AND 100'), nullable=False)


with app.app_context():
    db.create_all()
