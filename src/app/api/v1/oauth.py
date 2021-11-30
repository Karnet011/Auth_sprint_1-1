from datetime import datetime
from uuid import uuid4

from app.datastore import user_datastore
from flask import url_for, request, jsonify
from flask_restplus import Resource
from werkzeug import exceptions

from app.api.v1 import namespace
from app.database import session_scope
from app.models import SocialAccount
from app.oauth import oauth
from app.services.accounts import AccountsService
from app.services.storages import TokenStorageError


@namespace.route("/login/<string:name>")
class OauthLoginView(Resource):
    @namespace.doc("oauth login")
    def get(self, name: str):
        client = oauth.create_client(name)

        if not client:
            raise exceptions.NotFound()

        redirect_url = url_for("Api v1_oauth_authorization_view", name=name, _external=True)

        return client.authorize_redirect(redirect_url)


@namespace.route("/auth/<string:name>")
class OauthAuthorizationView(Resource):
    @namespace.doc("oauth authorization")
    def get(self, name: str):
        client = oauth.create_client(name)

        if not client:
            raise exceptions.NotFound()

        token = client.authorize_access_token()
        user_info = token.get("userinfo")
        
        if not user_info:
            user_info = client.userinfo()

        social_acc = SocialAccount.query.filter_by(social_id=user_info["sub"], social_name=name).first()

        if not social_acc:
            with session_scope():
                user = user_datastore.find_user(login=user_info["name"], email=user_info["email"])

                if not user:
                    user = user_datastore.create_user(
                        login=user_info["name"],
                        email=user_info["email"],
                        password=str(uuid4()),  # random password, will be changed by user
                    )

                user.last_login = datetime.utcnow()

            with session_scope() as session:
                social_acc = SocialAccount(social_id=user_info["sub"], social_name=name, user_id=user.id)
                session.add(social_acc)

        account_service = AccountsService(social_acc.user)
        account_service.record_entry_time(request)

        try:
            access_token, refresh_token = account_service.get_token_pair()
        except TokenStorageError:
            raise exceptions.Unauthorized()

        return jsonify(access_token=access_token, refresh_token=refresh_token)
