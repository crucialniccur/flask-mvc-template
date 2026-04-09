# server/seed.py

from app import app
from models import db
from models.user import User

with app.app_context():

    print("Clear old data since it is still dev mode not production mode.....")
    User.query.delete()

    print("Seed the Users init.....")
    users = [
        User(name="John", image_url=None),
        User(name="Stacy", image_url=None),
        User(name="Regina", image_url=None),
    ]

    db.session.add_all(users)
    db.session.commit()
    print("Done innit.....")
