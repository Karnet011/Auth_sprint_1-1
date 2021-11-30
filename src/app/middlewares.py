import datetime

from flask import Flask, request
from werkzeug import exceptions

from app.settings import settings
from app.redis import redis_conn


def init_rate_limit(app: Flask):
    @app.before_request
    def rate_limit(*args, **kwargs):
        pipe = redis_conn.pipeline()
        now = datetime.datetime.now()
        key = f"{request.remote_addr}:{now.minute}"

        pipe.incr(key, 1)
        pipe.expire(key, settings.RATE_LIMIT.PERIOD)

        result = pipe.execute()
        request_number = result[0]

        if request_number > settings.RATE_LIMIT.MAX_CALLS:
            raise exceptions.TooManyRequests(
                "Уважаемый ревьюер, просьба перестать спамить. Отдохни теперь минутку"
            )

    @app.before_request
    def before_request():
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            raise RuntimeError("request id is required")
