# server/controllers/user_controller.py


from flask import Blueprint
from flask_restful import Api, Resource
from models.user import User as Usermodel

user_bp = Blueprint("users", __name__, url_prefix="/users")
api = Api(user_bp)


class User(Resource):
    def get(self):

        user_dict = [user.to_dict() for user in Usermodel.query.all()]

        return user_dict, 200


api.add_resource(User, "/")
