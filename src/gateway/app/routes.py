import requests
from flask import Blueprint, request, jsonify

from .connector import NetworkConnector, Services

api = Blueprint('api', __name__)

connector = NetworkConnector()


@api.route('/libraries', methods=['GET'])
def list_libraries():
    response = connector.get(f'{Services.library.api}/libraries', params=dict(request.args))
    if not response.is_valid:
        return response.value

    return jsonify(response.value.json()), response.value.status_code


@api.route('/libraries/<library_uid>/books', methods=['GET'])
def get_library_books(library_uid):
    response = connector.get(f'{Services.library.api}/libraries/{library_uid}/books', params=dict(request.args))
    if not response.is_valid:
        return response.value

    return jsonify(response.value.json()), response.value.status_code


@api.route('/rating', methods=['GET'])
def get_rating():
    response = connector.get(f'{Services.rating.api}/rating')
    if not response.is_valid:
        return response.value

    return jsonify(response.value.json()), response.value.status_code


def fill_reservation(reservation):
    book_uid = reservation.get('bookUid')
    response = connector.get(f'{Services.library.api}/books/{book_uid}')
    if response.is_valid:
        reservation['book'] = response.value.json()
        reservation.pop('bookUid')

    library_uid = reservation.get('libraryUid')
    response = connector.get(f'{Services.library.api}/libraries/{library_uid}')
    if response.is_valid:
        reservation['library'] = response.value.json()
        reservation.pop('libraryUid')

    return reservation


@api.route('/reservations', methods=['GET'])
def list_reservations():
    response = connector.get(f'{Services.reservation.api}/reservations', headers=dict(request.headers))
    if not response.is_valid:
        return response.value

    reservations = response.value.json()
    for reservation in reservations:
        fill_reservation(reservation)

    return jsonify(reservations)


@api.route('/reservations', methods=['POST'])
def take_book():
    with requests.Session() as session:
        session.headers.update(request.headers)

        response = connector.get(f'{Services.reservation.api}/reservations', session)
        if not response.is_valid:
            return response.value
        rented = len(response.value.json())

        response = connector.get(f'{Services.rating.api}/rating', session)
        if not response.is_valid:
            return response.value
        stars = response.value.json()['stars']

        if rented >= stars:
            return jsonify({
                'message': 'Maximum rented books number has reached',
                'errors': []
            })

        args = request.json
        library_uid = args['libraryUid']
        book_uid = args['bookUid']
        r = session.patch(f"{Services.library.api}/libraries/{library_uid}/books/{book_uid}", json={'availableCount': 0})
        if r.status_code != 200:
            return jsonify(r.json()), r.status_code

        r = session.post(f'{Services.reservation.api}/reservations', json=request.json)
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
            f'{Services.reservation.api}/reservations/{reservation_uid}/return',
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
            f'{Services.library.api}/libraries/{library_uid}/books/{book_uid}',
            json={'availableCount': 1, 'condition': request.json['condition']}
        )

        rating = session.get(f'{Services.rating.api}/rating').json()
        rating['stars'] += rating_delta

        session.patch(f'{Services.rating.api}/rating', json=rating)

    return '', 204
