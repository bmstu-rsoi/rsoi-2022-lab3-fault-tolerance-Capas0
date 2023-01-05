from .base import app
from .routes import api, fallback, Services, MAX_FAILS
from flask import jsonify

app.register_blueprint(api, url_prefix='/api/v1')


@app.route('/manage/health', methods=['GET'])
def health():
    return '', 200
