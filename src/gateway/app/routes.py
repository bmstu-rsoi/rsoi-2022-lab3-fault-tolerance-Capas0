from queue import Queue

import requests
from flask import Blueprint, request, jsonify

from .connector import NetworkConnector, Services

api = Blueprint('api', __name__)

connector = NetworkConnector()
failed_requests = Queue(maxsize=10000)


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
    response = connector.get(f'{Services.rating.api}/rating', headers=dict(request.headers))
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

        response = connector.post(f'{Services.reservation.api}/reservations', session=session, json=request.json)
        if not response.is_valid:
            return response.value
        else:
            response = response.value
        if response.status_code != 201:
            return jsonify(response.json()), response.status_code

        reservation = fill_reservation(response.json())
        reservation['rating'] = {'stars': stars}

        args = request.json
        library_uid = args['libraryUid']
        book_uid = args['bookUid']
        response = connector.patch(
            f"{Services.library.api}/libraries/{library_uid}/books/{book_uid}",
            session=session,
            json={'availableCount': 0}
        )
        if not response.is_valid or response.value.status_code != 200:
            reservation_uid = reservation['reservationUid']
            connector.delete(f'{Services.reservation.api}/reservations/{reservation_uid}', session=session)

            if response.is_valid:
                return jsonify(response.value.json()), response.value.status_code
            else:
                return response.value

    return jsonify(reservation)


def change_rating(rating_delta, headers):
    response = connector.get(f'{Services.rating.api}/rating', headers=headers)
    if not response.is_valid:
        return False

    rating = response.value.json()
    rating['stars'] += rating_delta

    response = connector.patch(f'{Services.rating.api}/rating', json=rating, headers=headers)
    return response.is_valid


@api.route('reservations/<reservation_uid>/return', methods=['POST'])
def return_book(reservation_uid):
    response = connector.post(
        f'{Services.reservation.api}/reservations/{reservation_uid}/return',
        headers=dict(request.headers),
        json={'date': request.json['date']}
    )
    if not response.is_valid:
        return response.value
    else:
        response = response.value
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code

    reservation = fill_reservation(response.json())
    library_uid = reservation['library']['libraryUid']
    book_uid = reservation['book']['bookUid']

    request_data = {
        'url': f'{Services.library.api}/libraries/{library_uid}/books/{book_uid}',
        'headers': dict(request.headers),
        'json': {'availableCount': 1, 'condition': request.json['condition']}
    }

    response = connector.patch(**request_data)

    if not response.is_valid:
        failed_requests.put(lambda: connector.patch(**request_data).is_valid)

    rating_delta = 0
    if reservation['status'] == 'EXPIRED':
        rating_delta -= 10
    if reservation['book']['condition'] != request.json['condition']:
        rating_delta -= 10
    if rating_delta == 0:
        rating_delta = 1

    rating_request_data = {
        'rating_delta':  rating_delta,
        'headers': dict(request.headers)
    }

    if not change_rating(**rating_request_data):
        failed_requests.put(lambda: change_rating(**rating_request_data))

    return '', 204
