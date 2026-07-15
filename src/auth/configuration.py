from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()

mysqlUsername = os.environ["MYSQL_USERNAME"]
mysqlPassword = os.environ["MYSQL_PASSWORD"]
mysqlUrl = os.environ["MYSQL_URL"]
mysqlPort = os.environ["MYSQL_PORT"]

jwtSecret = os.environ["JWT_SECRET_KEY"]


class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{mysqlUsername}:{mysqlPassword}@{mysqlUrl}:{mysqlPort}/authentication"
    JWT_SECRET_KEY = jwtSecret
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours = 1)
