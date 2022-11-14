from datetime import date

from marshmallow import Schema, fields
from marshmallow_enum import EnumField

from .models import Reservation


class ReservationSchema(Schema):
    reservation_uid = fields.UUID(data_key='reservationUid')
    status = EnumField(Reservation.Status)
    start_date = fields.Date(data_key='startDate')
    till_date = fields.Date(data_key='tillDate')
    book_uid = fields.UUID(data_key='bookUid')
    library_uid = fields.UUID(data_key='libraryUid')


class TakeBookRequestSchema(Schema):
    book_uid = fields.UUID(data_key='bookUid')
    library_uid = fields.UUID(data_key='libraryUid')
    till_date = fields.Date(data_key='tillDate')


class ReturnBookRequestSchema(Schema):
    date = fields.Date()
