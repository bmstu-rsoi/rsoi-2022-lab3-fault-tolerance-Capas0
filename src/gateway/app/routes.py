from enum import Enum

import requests
from requests.exceptions import ConnectionError
from flask import Blueprint, request, jsonify, current_app

api = Blueprint('api', __name__)

reservation_api = 'http://reservation:8070/api/v1'
library_api = 'http://library:8060/api/v1'
rating_api = 'http://rating:8050/api/v1'


class Services(str, Enum):
    reservation = 'reservation'
    library = 'library'
    rating = 'rating'


fallback = {
    Services.reservation: 0,
    Services.library: 0,
    Services.rating: 0,
}
MAX_FAILS = 3


@api.route('/libraries', methods=['GET'])
def list_libraries():
    global fallback
    if fallback[Services.library] >= MAX_FAILS:
        return 'Library Service is unavailable', 500

    try:
        response = requests.get(f'{library_api}/libraries', params=dict(request.args))
        fallback[Services.library] = 0
        return jsonify(response.json()), response.status_code
    except ConnectionError:
        fallback[Services.library] += 1
        current_app.logger.warning('Library Service is unavailable')
        return 'Library Service is unavailable', 500


@api.route('/libraries/<library_uid>/books', methods=['GET'])
def get_library_books(library_uid):
    global fallback
    if fallback[Services.library] >= MAX_FAILS:
        return 'Library Service is unavailable', 500

    try:
        response = requests.get(f'{library_api}/libraries/{library_uid}/books', params=dict(request.args))
        fallback[Services.library] = 0
        return jsonify(response.json()), response.status_code
    except ConnectionError:
        fallback[Services.library] += 1
        current_app.logger.warning('Library Service is unavailable')
        return 'Library Service is unavailable', 500


@api.route('/rating', methods=['GET'])
def get_rating():
    global fallback
    if fallback[Services.rating] >= MAX_FAILS:
        return 'Rating Service is unavailable', 500

    try:
        response = requests.get(f'{rating_api}/rating', headers=dict(request.headers))
        fallback[Services.rating] = 0
        return jsonify(response.json()), response.status_code
    except ConnectionError:
        fallback[Services.rating] += 1
        current_app.logger.warning('Rating Service is unavailable')
        return 'Rating Service is unavailable', 500


def fill_reservation(reservation):
    global fallback

    if fallback[Services.library] >= MAX_FAILS:
        return reservation

    try:
        book_uid = reservation.get('bookUid')
        reservation['book'] = requests.get(f'{library_api}/books/{book_uid}').json()
        reservation.pop('bookUid')

        library_uid = reservation.get('libraryUid')
        reservation['library'] = requests.get(f'{library_api}/libraries/{library_uid}').json()
        reservation.pop('libraryUid')

        fallback[Services.library] = 0
    except ConnectionError:
        fallback[Services.library] += 1
        current_app.logger.warning('Library Service is unavailable')

    return reservation


@api.route('/reservations', methods=['GET'])
def list_reservations():
    global fallback
    if fallback[Services.reservation] >= MAX_FAILS:
        return 'Reservation Service is unavailable', 500

    try:
        reservations = requests.get(f'{reservation_api}/reservations', headers=dict(request.headers)).json()
        for reservation in reservations:
            fill_reservation(reservation)

        return jsonify(reservations)
    except ConnectionError:
        fallback[Services.reservation] += 1
        current_app.logger.warning('Reservation Service is unavailable')
        return 'Reservation Service is unavailable', 500


@api.route('/reservations', methods=['POST'])
def take_book():
    with requests.Session() as session:
        session.headers.update(request.headers)

        rented = len(session.get(f'{reservation_api}/reservations').json())
        stars = session.get(f'{rating_api}/rating').json()['stars']
        if rented >= stars:
            return jsonify({
                'message': 'Maximum rented books number has reached',
                'errors': []
            })

        args = request.json
        library_uid = args['libraryUid']
        book_uid = args['bookUid']
        r = session.patch(f"{library_api}/libraries/{library_uid}/books/{book_uid}", json={'availableCount': 0})
        if r.status_code != 200:
            return jsonify(r.json()), r.status_code

        r = session.post(f'{reservation_api}/reservations', json=request.json)
        if r.status_code != 201:
            return jsonify(r.json()), r.status_code

        reservation = fill_reservation(r.json())
        reservation['rating'] = {'stars': stars}

    return jsonify(reservation)


@api.route('reservations/<reservation_uid>/return', methods=['POST'])
def return_book(reservation_uid):
    with requests.Session() as session:
        session.headers.update(request.headers)

        r = session.post(
            f'{reservation_api}/reservations/{reservation_uid}/return',
            json={'date': request.json['date']}
        )
        if r.status_code != 200:
            return jsonify(r.json()), r.status_code

        reservation = fill_reservation(r.json())
        library_uid = reservation['library']['libraryUid']
        book_uid = reservation['book']['bookUid']

        rating_delta = 0
        if reservation['status'] == 'EXPIRED':
            rating_delta -= 10
        if reservation['book']['condition'] != request.json['condition']:
            rating_delta -= 10
        if rating_delta == 0:
            rating_delta = 1

        session.patch(
            f'{library_api}/libraries/{library_uid}/books/{book_uid}',
            json={'availableCount': 1, 'condition': request.json['condition']}
        )

        rating = session.get(f'{rating_api}/rating').json()
        rating['stars'] += rating_delta

        session.patch(f'{rating_api}/rating', json=rating)

    return '', 204
