import logging
from threading import Thread

from flask.cli import FlaskGroup
from gevent import monkey

monkey.patch_all()
from app import app
from watchdog import fallback_watchdog, repeat_watchdog

cli = FlaskGroup(app)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)

Thread(target=fallback_watchdog, daemon=True).start()
Thread(target=repeat_watchdog, daemon=True).start()

if __name__ == "__main__":
    cli()
