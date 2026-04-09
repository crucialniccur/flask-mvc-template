# server/controllers/user_controller.py


from flask import Blueprint, request
from flask_restful import Api, Resource
from models import db
from models.user import User as Usermodel
from utils.cloudinary_helper import upload_image

user_bp = Blueprint("users", __name__, url_prefix="/users")
api = Api(user_bp)


class User(Resource):
    def get(self):

        users = [user.to_dict() for user in Usermodel.query.all()]

        return users, 200

    def post(self):
        name = request.form.get("name")
        file = request.files.get("image")

        if not name:
            return {"error": "name is required"}, 400

        image_url = None
        if file:
            image_url = upload_image(file)

        user = Usermodel(name=name, image_url=image_url)
        db.session.add(user)
        db.session.commit()

        return user.to_dict(), 201


api.add_resource(User, "/")
