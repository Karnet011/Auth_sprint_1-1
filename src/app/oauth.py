from authlib.integrations.flask_client import OAuth
from flask import Flask

from app.settings import settings

oauth = OAuth()

oauth.register(
    name="google",
    server_metadata_url=settings.OAUTH.GOOGLE_METADATA_URL,  # extra request to google
    client_kwargs={
        "scope": "openid email profile"
    }
)

# oauth.register(
#     name="yandex",
#     api_base_url="https://oauth.yandex.ru",
#     authorize_url=settings.OAUTH.YANDEX_AUTHORIZE_URL,
# )


def init_oauth(app: Flask):
    app.config["GOOGLE_CLIENT_ID"] = settings.OAUTH.GOOGLE_CLIENT_ID
    app.config["GOOGLE_CLIENT_SECRET"] = settings.OAUTH.GOOGLE_CLIENT_SECRET

    app.config["YANDEX_CLIENT_ID"] = settings.OAUTH.YANDEX_CLIENT_ID
    app.config["YANDEX_CLIENT_SECRET"] = settings.OAUTH.YANDEX_CLIENT_SECRET
    app.config["YANDEX_AUTHORIZE_URL"] = settings.OAUTH.YANDEX_AUTHORIZE_URL

    oauth.init_app(app)
