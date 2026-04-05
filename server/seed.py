# server/seed.py

from app import app
from models import db
from models.user import User

with app.app_context():

    print("Clear old data since it is still dev mode not production mode.....")
    User.query.delete()

    print("Seed the Users init.....")
    users = [User(name="John"), User(name="Stacy"), User(name="Regina")]

    db.session.add_all(users)
    db.session.commit()
    print("Done innit.....")
