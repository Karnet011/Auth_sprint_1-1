from enum import Enum
from uuid import uuid4

from flask_security import UserMixin, RoleMixin

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db


def create_partition_history(target, connection, **kw) -> None:
    """creating partition by user_sign_in"""
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_smart" PARTITION OF "auth_history" FOR VALUES IN ('smart')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_mobile" PARTITION OF "auth_history" FOR VALUES IN ('mobile')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_web" PARTITION OF "auth_history" FOR VALUES IN ('web')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_web" PARTITION OF "auth_history" FOR VALUES IN ('PostmanRuntime/7.28.4')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_sign_in_web"
         PARTITION OF "auth_history" FOR VALUES NOT IN ('smart') AND 
                                         VALUES NOT IN ('mobile') AND
                                         VALUES NOT IN ('web')"""
    )


def create_partition_user(target, connection, **kw) -> None:
    """creating partition by user_sign_in"""
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "user_registration"
         PARTITION OF date_part('year', 'created_on') FOR VALUES IN (date_part('year', now()))"""
    )


class DefaultRoleEnum(str, Enum):
    guest = "guest"
    superuser = "superuser"
    staff = "staff"


class MethodsExtensionMixin:
    def update_or_skip(self, **kwargs) -> tuple[db.Model, bool]:
        is_updated = False

        for key, val in kwargs.items():
            if not hasattr(self, key) or getattr(self, key, None) == val:
                continue

            setattr(self, key, val)

            if not is_updated:
                is_updated = True

        return self, is_updated


class TimestampMixin:
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now()
    )


class RolesUsers(db.Model):
    __tablename__ = "roles_users"

    id = db.Column(db.BigInteger(), primary_key=True)
    user_id = db.Column("user_id", UUID(as_uuid=True), db.ForeignKey("users.id"))
    role_id = db.Column("role_id", UUID(as_uuid=True), db.ForeignKey("roles.id"))


class Role(TimestampMixin, db.Model, RoleMixin, MethodsExtensionMixin):
    __tablename__ = "roles"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False
    )
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return f"<Role {self.name}>"

    class Meta:
        PROTECTED_ROLE_NAMES = (
            DefaultRoleEnum.guest.value,
            DefaultRoleEnum.superuser.value,
            DefaultRoleEnum.staff.value,
        )


class User(TimestampMixin, db.Model, UserMixin, MethodsExtensionMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("id", "created_on"),
        {
            "postgresql_partition_by": "LIST (created_on)",
            "listeners": [("after_create", create_partition_user)],
        },
    )

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False
    )
    login = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    _password = db.Column("password", db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    last_login = db.Column(db.DateTime())
    roles = db.relationship(
        "Role",
        secondary="content.roles_users",
        backref=db.backref("users", lazy="dynamic"),
    )

    def __str__(self) -> str:
        return f"<User {self.login}>"

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self._password, password)

    @property
    def is_admin(self) -> bool:
        return self.has_role(DefaultRoleEnum.staff.value) or self.has_role(
            DefaultRoleEnum.superuser.value
        )

    @property
    def roles_names_list(self) -> list[str]:
        return [role.name for role in self.roles]


class AuthHistory(db.Model):
    __tablename__ = "auth_history"
    __table_args__ = (
        UniqueConstraint("id", "device"),
        {
            "postgresql_partition_by": "LIST (device)",
            "listeners": [("after_create", create_partition_history)],
        },
    )

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False
    )
    user_id = db.Column("user_id", UUID(as_uuid=True), db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_agent = db.Column(db.Text, nullable=False)
    ip_addr = db.Column(db.String(100))

    device = db.Column(db.Text, primary_key=True)

class SocialAccount(db.Model):
    __tablename__ = "social_accounts"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False
    )
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    user = db.relationship(User, backref=db.backref("social_accounts", lazy=True))

    social_id = db.Column(db.String(255), nullable=False)
    social_name = db.Column(db.String(255), nullable=False)

    __table_args__ = (db.UniqueConstraint("social_id", "social_name", name="social_uc"), )

    def __str__(self) -> str:
        return f"<SocialAccount {self.social_name}:{self.user_id}>"
