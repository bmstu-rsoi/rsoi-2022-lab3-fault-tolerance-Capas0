from datetime import date

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import DataError

from .base import db
from .models import Reservation
from .schemas import ReservationSchema, TakeBookRequestSchema

api = Blueprint('api', __name__)


def format_errors(messages):
    for field, errors in messages.items():
        for error in errors:
            yield {'field': field, 'error': error}


def format_validation_error(text, error):
    return {
        'message': text,
        'errors': list(format_errors(error.messages))
    }


@api.route('/reservations', methods=['GET'])
def list_reservations():
    username = request.headers.get('X-User-Name')

    reservations = db.session.execute(
        db.select(Reservation).where(
            Reservation.username == username,
            Reservation.status == Reservation.Status.RENTED
        )
    ).scalars().all()
    return jsonify(ReservationSchema().dump(reservations, many=True)), 200


@api.route('/reservations', methods=['POST'])
def take_book():
    username = request.headers.get('X-User-Name')
    try:
        data = TakeBookRequestSchema().load(request.json)
        reservation = Reservation(username=username, start_date=date.today(), status=Reservation.Status.RENTED, **data)
        db.session.add(reservation)
        db.session.commit()
        return ReservationSchema().dump(reservation), 201
    except ValidationError as err:
        return jsonify(format_validation_error('Invalid data', err)), 400


@api.route('reservations/<reservation_uid>/return', methods=['POST'])
def return_book(reservation_uid):
    username = request.headers.get('X-User-Name')
    return_date = date.fromisoformat(request.json['date'])
    try:
        reservation = db.session.execute(
            db.select(Reservation)
            .where(Reservation.username == username, Reservation.reservation_uid == reservation_uid)
        ).scalars().one()
    except DataError:
        return jsonify({'message': f'Reservation with UID "{reservation_uid}"not found'}), 404

    if return_date > reservation.till_date:
        reservation.status = Reservation.Status.EXPIRED
    else:
        reservation.status = Reservation.Status.RETURNED
    db.session.commit()

    return jsonify(ReservationSchema().dump(reservation)), 200


@api.route('reservations/<reservation_uid>', methods=['DELETE'])
def revoke_reservation(reservation_uid):
    username = request.headers.get('X-User-Name')
    try:
        db.session.execute(
            db.delete(Reservation)
            .where(Reservation.username == username, Reservation.reservation_uid == reservation_uid)
        )
    except DataError:
        return jsonify({'message': f'Reservation with UID "{reservation_uid}"not found'}), 404

    return 'Deleted', 200
