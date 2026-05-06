# server/controllers/user_controller.py


from flask import Blueprint, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required
from flask_restful import Api, Resource
from models import db
from models.user import (
    User as UserModel,  # Remember to user UseModel when querying the database
)
from utils.cloudinary_helper import upload_image

user_bp = Blueprint("users", __name__, url_prefix="/users")
api = Api(user_bp)
bcrypt = Bcrypt()


class UserList(Resource):
    @jwt_required()
    def get(self):
        users = [user.to_dict() for user in UserModel.query.all()]

        return users, 200


class UserByID(Resource):
    @jwt_required()
    def get(self, id):
        user = UserModel.query.get(id)

        if not user:
            return {"error": "User not found"}, 404
        return user.to_dict(), 200


class Register(Resource):
    def post(self):
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        file = request.files.get("image")

        if not name or not email or not password:
            return {"error": "Name, email and password required"}, 400

        if UserModel.query.filter_by(email=email).first():
            return {"error": "email already registered"}, 409

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        image_url = None
        if file:
            image_url = upload_image(file)

        user = UserModel(
            name=name,
            email=email,
            password_hash=password_hash,
            image_url=image_url,
        )
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))

        return {"user": user.to_dict(), "access_token": access_token}, 201


class Login(Resource):
    def post(self):
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return {"error": "email and password are required"}, 400

        user = UserModel.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return {"error": "Invalid credentials"}, 401

        access_token = create_access_token(identity=str(user.id))

        return {"user": user.to_dict(), "access_token": access_token}, 200


api.add_resource(UserList, "/")
api.add_resource(UserByID, "/<int:id>")
api.add_resource(Register, "/register")
api.add_resource(Login, "/login")
