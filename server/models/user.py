# server/models/user.py

from sqlalchemy_serializer import SerializerMixin

from . import db


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    image_url = db.Column(db.String, nullable=True)
    password_hash = db.Column(db.String, nullable=False)

    serialize_rules = ("-password_hash",)

    def __repr__(self):
        return f"User {self.name}"
