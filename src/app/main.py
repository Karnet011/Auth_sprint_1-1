import http

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, current_user
from flask_restplus import Api, Resource, Namespace, fields
from flask_security import SQLAlchemyUserDatastore, Security
from sqlalchemy.exc import IntegrityError
from werkzeug import exceptions

from app.api.admin.utils import admin_required
from app.api.parsers import role_parser
from app.api.schemas import role_schema
from app.database import init_db, db, session_scope
from app.models import User, Role
from app.settings import settings

app = Flask(settings.FLASK_APP)
app.config["DEBUG"] = settings.DEBUG

init_db(app)
# init_api(app)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()

security.init_app(app, user_datastore)

app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)


api = Api(
    title="Auth API",
    version="1.0",
    description="Auth API operations",
)

namespace = Namespace("admin", path="/admin", description="Auth admin API")
api_namespace = Namespace("auth", path="/api", description="Auth API operations")

api.add_namespace(namespace)
api.add_namespace(api_namespace)


api.init_app(app)

admin_role_schema = namespace.model("Role", role_schema)


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()


login_schema = namespace.model("Login", {
    "access_token": fields.String(),
    "refresh_token": fields.String(),
})

login_parser = namespace.parser()
login_parser.add_argument("login", type=str, required=True, help="Login")
login_parser.add_argument("password", type=str, required=True, help="Password")


class BaseJWTResource(Resource):
    method_decorators = (jwt_required(), )


class BaseJWTAdminResource(Resource):
    method_decorators = (admin_required(), )


@namespace.route("/login")
class LoginView(Resource):
    @namespace.doc("login")
    @namespace.expect(login_parser)
    # @namespace.marshal_with(login_schema, code=http.HTTPStatus.OK)
    def post(self):
        args = login_parser.parse_args()

        user = User.query.filter_by(login=args["login"]).one_or_none()

        if not user or not user.check_password(args["password"]):
            return exceptions.Unauthorized

        access_token = create_access_token(
            identity=user, additional_claims={
                "is_admin": user.is_admin,
            }
        )
        refresh_token = create_refresh_token(identity=user)

        return jsonify(access_token=access_token, refresh_token=refresh_token)


# @jwt.token_in_blocklist_loader
# def check_if_token_is_revoked(jwt_header, jwt_payload):
#     jti = jwt_payload["jti"]
#     token_in_redis = jwt_redis_blocklist.get(jti)
#     return token_in_redis is not None


refresh_parser = api.parser()
refresh_parser.add_argument("Refresh", location='args', help="Refresh query param", required=True)


@namespace.route("/refresh")
class RefreshView(Resource):
    @namespace.doc("refresh")
    @namespace.expect(refresh_parser)
    def post(self):
        args = login_parser.parse_args()

        user = User.query.filter_by(login=args["login"]).one_or_none()

        if not user or not user.check_password(args["password"]):
            return exceptions.Unauthorized

        access_token = create_access_token(
            identity=user, additional_claims={
                "is_admin": user.is_admin,
            }
        )
        refresh_token = create_refresh_token(identity=user)

        return jsonify(access_token=access_token, refresh_token=refresh_token)


@namespace.route("/who_am_i")
class SomeView(BaseJWTResource):
    @namespace.doc("who_am_i")
    def get(self):
        return jsonify(
            id=current_user.id,
            login=current_user.login,
            email=current_user.email,
            roles=current_user.roles,
        )


@namespace.route("/roles")
class RolesView(BaseJWTAdminResource):
    @namespace.doc("get list of roles")
    @namespace.marshal_with(admin_role_schema, as_list=True, code=http.HTTPStatus.OK)
    def get(self):
        return Role.query.all()

    @namespace.doc("create role", responses={
        http.HTTPStatus.BAD_REQUEST: "Bad Request",
        http.HTTPStatus.CREATED: "Created",
    })
    @namespace.expect(role_parser)
    @namespace.marshal_with(admin_role_schema, code=http.HTTPStatus.CREATED)
    def post(self):
        new_role = Role(**role_parser.parse_args())

        try:
            with session_scope() as session:
                session.add(new_role)
        except IntegrityError:
            raise exceptions.BadRequest("Already exists.")

        return new_role, http.HTTPStatus.CREATED


@namespace.route("/roles/<int:role_id>")
class SpecificRolesView(BaseJWTAdminResource):
    @namespace.doc("change role", responses={
        http.HTTPStatus.NOT_FOUND: "Not Found",
        http.HTTPStatus.BAD_REQUEST: "Bad Request",
    })
    @namespace.expect(role_parser)
    @namespace.marshal_with(admin_role_schema, code=http.HTTPStatus.OK)
    def patch(self, role_id: int):
        role = Role.query.get_or_404(id=role_id)

        args = role_parser.parse_args()

        if args["name"] in Role.Meta.PROTECTED_ROLE_NAMES:
            raise exceptions.BadRequest("This role is protected.")

        try:
            with session_scope():
                role.update_or_skip(**role_parser.parse_args())
        except IntegrityError:
            raise exceptions.BadRequest("Already exists.")

        return role

    @namespace.doc("delete role", responses={
        http.HTTPStatus.NOT_FOUND: "Not Found",
        http.HTTPStatus.BAD_REQUEST: "Bad Request",
        http.HTTPStatus.NO_CONTENT: "No Content",
    })
    @namespace.marshal_with("", code=http.HTTPStatus.NO_CONTENT)
    def delete(self, role_id: int):
        role = Role.query.get_or_404(id=role_id)

        args = role_parser.parse_args()

        if args["name"] in Role.Meta.PROTECTED_ROLE_NAMES:
            raise exceptions.BadRequest("This role is protected.")

        with session_scope():
            role.is_active = False

        return "", http.HTTPStatus.NO_CONTENT


app.app_context().push()
