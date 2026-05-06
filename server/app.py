from config import Config

# Import blueprints
from controllers.user_controller import user_bp
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    with app.app_context():
        from models import user  # noqa: F401

    # Register Blueprints
    app.register_blueprint(user_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
