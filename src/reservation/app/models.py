import enum
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Date, Enum
from sqlalchemy.dialects.postgresql import UUID

from .base import db, app


class Reservation(db.Model):
    __tablename__ = 'reservation'

    class Status(enum.Enum):
        RENTED = 'RENTED'
        RETURNED = 'RETURNED'
        EXPIRED = 'EXPIRED'

    id = Column(Integer, primary_key=True)
    reservation_uid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    username = Column(String(80), nullable=False)
    book_uid = Column(UUID(as_uuid=True), nullable=False)
    library_uid = Column(UUID(as_uuid=True), nullable=False)
    status = Column(Enum(Status), nullable=False)
    start_date = Column(Date(), nullable=False)
    till_date = Column(Date(), nullable=False)


with app.app_context():
    db.create_all()
