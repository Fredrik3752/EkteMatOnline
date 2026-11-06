"""Ekte Mat Online – Flask application factory."""
import os

from dotenv import load_dotenv
from flask import Flask

from app.config import Config


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    if not os.path.isabs(app.config["DATABASE"]):
        app.config["DATABASE"] = os.path.join(app.instance_path, app.config["DATABASE"])

    from app.models.repositories import database
    database.init_app(app)

    from app.controllers.shop import bp as shop_bp
    app.register_blueprint(shop_bp)

    return app
