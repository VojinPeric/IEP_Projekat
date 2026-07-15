import re

from flask import Blueprint, request

from flask_jwt_extended import create_access_token, get_jwt_identity
from sqlalchemy import and_;

from models import User, Role, database
from shared.credential_decorators import role_check;

auth_blueprint = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

def correct_password_format(password):
    return len(password) >= 8

@auth_blueprint.route("/register", methods = ["POST"])
def register():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if forename == "":
        return { "message": "Field forename is missing." }, 400
    if surname == "":
        return { "message": "Field surname is missing." }, 400
    if email == "":
        return { "message": "Field email is missing." }, 400
    if password == "":
        return { "message": "Field password is missing." }, 400

    if len(forename) > 256:
        return { "message": "Forename must be at most 256 characters." }, 400
    if len(surname) > 256:
        return { "message": "Surname must be at most 256 characters." }, 400
    if len(email) > 256:
        return { "message": "Email must be at most 256 characters." }, 400
    if len(password) > 256:
        return { "message": "Password must be at most 256 characters." }, 400

    if not EMAIL_RE.match(email):
        return { "message": "Invalid email." }, 400
    if not correct_password_format(password):
        return { "message": "Invalid password." }, 400
    
    user = User.query.filter(User.email == email).first()
    if user is not None:
        return { "message": "Email already exists." }, 400
    
    user = User(email = email, password = password, forename = forename, surname = surname, role = Role.EMPLOYEE)
    database.session.add(user)
    database.session.commit()

    return {}, 200

@auth_blueprint.route("/login", methods = ["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if email == "":
        return { "message": "Field email is missing." }, 400
    if password == "":
        return { "message": "Field password is missing." }, 400

    if len(email) > 256:
        return { "message": "Email must be at most 256 characters." }, 400
    if len(password) > 256:
        return { "message": "Password must be at most 256 characters." }, 400

    if not EMAIL_RE.match(email):
        return { "message": "Invalid email." }, 400
    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if user is None:
        return { "message": "Invalid credentials." }, 400
    
    additionalClaims = {
            "forename": user.forename,
            "surname": user.surname,
            "role": user.role.value
    }

    accessToken = create_access_token(identity = user.email, additional_claims = additionalClaims)
    return { "accessToken": accessToken }, 200

@auth_blueprint.route("/delete", methods = ["POST"])
@role_check(None)
def delete():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()
    if user is None:
        return { "message": "Unknown user." }, 400
    
    User.query.filter(User.email == email).delete()
    database.session.commit()

    return {}, 200


