from dataclasses import dataclass
from enum import Enum
from typing import Union

import requests
from requests.exceptions import ConnectionError
from flask import current_app, jsonify

reservation_api = 'http://reservation:8070/api/v1'
library_api = 'http://library:8060/api/v1'
rating_api = 'http://rating:8050/api/v1'


class Services(str, Enum):
    reservation = 'Reservation'
    library = 'Library'
    rating = 'Rating'

    @property
    def api(self):
        if self is Services.reservation:
            return reservation_api
        elif self is Services.library:
            return library_api
        elif self is Services.rating:
            return rating_api


fallback = {
    Services.reservation: 0,
    Services.library: 0,
    Services.rating: 0,
}
MAX_FAILS = 3


@dataclass
class ResponseWrapper:
    is_valid: bool
    value: Union[tuple, requests.Response]


def get_service(url: str):
    if url.startswith(reservation_api):
        return Services.reservation
    elif url.startswith(library_api):
        return Services.library
    else:
        return Services.rating


def check_fall(func):
    def wrapper(url: str, *args, **kwargs):
        service = get_service(url)

        global fallback
        if fallback[service] < MAX_FAILS:
            try:
                response = func(url, *args, **kwargs)
                fallback[service] = 0
                return ResponseWrapper(is_valid=True, value=response)
            except ConnectionError:
                fallback[service] += 1
                current_app.logger.warning(f'{service.value} Service unavailable')

        return ResponseWrapper(
            is_valid=False,
            value=(jsonify(message=f'{service.value} Service unavailable'), 503)
        )

    return wrapper


class NetworkConnector:

    @staticmethod
    @check_fall
    def get(url: str, session=None, **kwargs):
        if session is None:
            return requests.get(url, **kwargs)
        else:
            return session.get(url, **kwargs)

    @staticmethod
    @check_fall
    def patch(url: str, session=None, **kwargs):
        if session is None:
            return requests.patch(url, **kwargs)
        else:
            return session.patch(url, **kwargs)

    @staticmethod
    @check_fall
    def post(url: str, session=None, **kwargs):
        if session is None:
            return requests.post(url, **kwargs)
        else:
            return session.post(url, **kwargs)

    @staticmethod
    @check_fall
    def delete(url: str, session=None, **kwargs):
        if session is None:
            return requests.delete(url, **kwargs)
        else:
            return session.delete(url, **kwargs)
