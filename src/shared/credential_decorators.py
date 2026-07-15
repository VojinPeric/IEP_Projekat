
from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError

# checks role if any, if none checks token
def role_check ( role ):
    def wrapper ( function ):
        @wraps ( function )
        def decorator ( *arguments, **keywordArguments ):
            verify_jwt_in_request()
            claims = get_jwt()
            if role is None or claims.get("role") == role.value:
                return function ( *arguments, **keywordArguments );
            else:
                raise NoAuthorizationError("Missing Authorization Header")
        return decorator
    return wrapper;