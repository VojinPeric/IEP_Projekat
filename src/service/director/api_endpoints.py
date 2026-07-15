import json
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, request
from redis import Redis

from shared.credential_decorators import role_check
from auth.models import Role
from service.shared.configuration import Configuration
from service.shared.models import Property, properties

director_blueprint = Blueprint("director", __name__)

@director_blueprint.route("/pending_orders", methods = ["GET"])
@role_check(Role.DIRECTOR)
def pending_orders():
    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        entries = redis.lrange(Configuration.REDIS_ORDER_LIST, 0, -1)

    orders = [json.loads(entry) for entry in entries]

    return { "orders": orders }, 200

@director_blueprint.route("/decision", methods = ["POST"])
@role_check(Role.DIRECTOR)
def decision():
    uuid = request.json.get("uuid", "")
    approved = request.json.get("approved", None)

    if len(uuid) == 0:
        return { "message": "Field uuid is missing." }, 400
    if approved is None:
        return { "message": "Field approved is missing." }, 400
    if not isinstance(approved, bool) :
        return { "message": "Invalid decision." }, 400

    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        entries = redis.lrange(Configuration.REDIS_ORDER_LIST, 0, -1)

    order = None
    matched_entry = None
    for entry in entries:
        parsed = json.loads(entry)
        if parsed.get("uuid") == uuid:
            order = parsed
            matched_entry = entry
            break

    if order is None:
        return { "message": "Invalid uuid." }, 400

    if approved:
        if order["order_type"] == "BUY":
            property = Property(
                name = order["name"],
                categories = order["categories"],
                buying_price = order["buying_price"],
                buying_date = datetime.now(timezone.utc),
                info = order["info"]
            )
            properties.insert_one(property.to_document())
        elif order["order_type"] == "SELL":
            properties.update_one(
                { "_id": ObjectId(order["id"]) },
                { "$set": { "selling_price": order["selling_price"], "selling_date": datetime.now(timezone.utc) } }
            )

    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        redis.lrem(Configuration.REDIS_ORDER_LIST, 1, matched_entry)

    return {}, 200

@director_blueprint.route("/report", methods = ["GET"])
@role_check(Role.DIRECTOR)
def report():
    pipeline = [
        { "$match": { "selling_price": { "$ne": None }, "selling_date": { "$ne": None } } },
        { "$unwind": "$categories" },
        { "$group": {
            "_id": "$categories",
            "spent": { "$sum": "$buying_price" },
            "earned": { "$sum": "$selling_price" }
        } },
        { "$project": { "_id": 0, "category": "$_id", "spent": 1, "earned": 1 } },
        { "$sort": { "earned": -1, "spent": 1, "category": 1 } }
    ]

    statistics = list(properties.aggregate(pipeline))

    return { "statistics": statistics }, 200
