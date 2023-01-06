from time import sleep

import requests
from requests.exceptions import ConnectionError

from app import app, fallback, Services, MAX_FAILS, failed_requests

health = {
    Services.reservation: 'http://reservation:8070/manage/health',
    Services.library: 'http://library:8060/manage/health',
    Services.rating: 'http://rating:8050/manage/health',
}

WATCHDOG_INTERVAL = 10


def fallback_watchdog():
    with app.app_context():
        while True:
            for service, fails in fallback.items():
                if fails < MAX_FAILS:
                    continue
                try:
                    requests.get(health[service])
                    fallback[service] = 0
                    app.logger.info(f'Service {service.value} is up')
                except ConnectionError:
                    pass
            sleep(WATCHDOG_INTERVAL)


def repeat_watchdog():
    with app.app_context():
        while True:
            func = failed_requests.get()
            if not func():
                failed_requests.put(func)
                sleep(WATCHDOG_INTERVAL)
