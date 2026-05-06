# server/seed.py
from app import app
from flask_bcrypt import Bcrypt
from models import db
from models.user import User

bcrypt = Bcrypt()

with app.app_context():
    print("Clearing old data...")
    User.query.delete()

    print("Seeding users...")
    users = [
        User(
            name="Alice",
            email="alice@test.com",
            password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
            image_url=None,
        ),
        User(
            name="Bob",
            email="bob@test.com",
            password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
            image_url=None,
        ),
    ]

    db.session.add_all(users)
    db.session.commit()
    print("Done!")
