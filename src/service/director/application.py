from flask import Flask
from flask_jwt_extended import JWTManager

from service.shared.configuration import Configuration
from api_endpoints import director_blueprint

application = Flask(__name__)
application.config.from_object(Configuration)

application.register_blueprint (director_blueprint)

jwt = JWTManager(application)

if (__name__ == "__main__"):
    application.run(debug = True, host="0.0.0.0", port=5001)