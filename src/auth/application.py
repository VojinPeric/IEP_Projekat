from flask import Flask
from flask_jwt_extended import JWTManager

from configuration import Configuration
from api_endpoints import auth_blueprint
from models import database;

application = Flask(__name__)
application.config.from_object(Configuration)

application.register_blueprint (auth_blueprint, url_prefix = "/auth")

jwt = JWTManager(application)

if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug = True, host="0.0.0.0", port=5001)

