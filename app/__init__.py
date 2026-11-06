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

    from app.seed import seed_command
    app.cli.add_command(seed_command)

    from app.controllers import account, admin, shop
    from app.controllers.auth import load_logged_in_user
    from app.controllers.csrf import check_csrf, csrf_token
    from app.controllers.errors import register_error_handlers
    from app.models.money import format_nok, ore_to_input

    app.before_request(load_logged_in_user)
    app.before_request(check_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.jinja_env.filters["nok"] = format_nok
    app.jinja_env.filters["nok_input"] = ore_to_input
    register_error_handlers(app)

    app.register_blueprint(shop.bp)
    app.register_blueprint(account.bp)
    app.register_blueprint(admin.bp)

    return app
