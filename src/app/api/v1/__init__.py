from flask_restplus import Namespace

namespace = Namespace("Api v1", path="/api/v1", description="Auth API v1 operations")

from app.api.v1 import accounts, users, oauth
