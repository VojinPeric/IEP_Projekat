import os

from dotenv import load_dotenv

load_dotenv()

mongoUsername = os.environ["MONGO_USERNAME"]
mongoPassword = os.environ["MONGO_PASSWORD"]
mongoUrl = os.environ["MONGO_URL"]
mongoPort = os.environ["MONGO_PORT"]

redisUrl = os.environ["REDIS_URL"]
redisPort = os.environ["REDIS_PORT"]

jwtSecret = os.environ["JWT_SECRET_KEY"]

ganacheUrl = os.environ["GANACHE_URL"]
ganachePort = os.environ["GANACHE_PORT"]


class Configuration ( ):
    MONGO_URI = f"mongodb://{mongoUsername}:{mongoPassword}@{mongoUrl}:{mongoPort}"
    JWT_SECRET_KEY = jwtSecret
    REDIS_HOST = redisUrl
    REDIS_PORT = redisPort
    REDIS_ORDER_LIST = "ORDERS"
    GANACHE_URI = f"http://{ganacheUrl}:{ganachePort}"
