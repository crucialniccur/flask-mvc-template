# server/models/user.py

from sqlalchemy_serializer import SerializerMixin

from . import db


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=True)

    def __repr__(self):
        return f"User {self.name}"
