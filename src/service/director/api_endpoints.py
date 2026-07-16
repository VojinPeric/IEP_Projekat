import json
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, request
from redis import Redis
from web3 import Web3

from shared.credential_decorators import role_check
from auth.models import Role
from service.shared.configuration import Configuration
from service.shared.models import Property, properties
from service.shared.blockchain import admin_account, deploy_proposal_contract

director_blueprint = Blueprint("director", __name__)

@director_blueprint.route("/pending_orders", methods = ["GET"])
@role_check(Role.DIRECTOR)
def pending_orders():
    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        entries = redis.lrange(Configuration.REDIS_ORDER_LIST, 0, -1)

    orders = []
    for entry in entries:
        order = json.loads(entry)
        order.pop("contract_address", None)
        orders.append(order)

    return { "orders": orders }, 200

def blockchain_decision(order, matched_entry, voters):
    if voters is None or (isinstance(voters, list) and len(voters) == 0):
        return { "message": "Field voters is missing." }, 400
    if not isinstance(voters, list) or not all(isinstance(voter, str) for voter in voters):
        return { "message": "Voters must be a list of addresses." }, 400
    if len(voters) % 2 == 0:
        return { "message": "Even number of voters." }, 400
    if not all(Web3.is_address(voter) for voter in voters):
        return { "message": "Invalid voter address." }, 400

    proposal_contract = deploy_proposal_contract(voters)

    approve_transaction = proposal_contract.functions.approve().build_transaction({ "from": admin_account, "gas": 300000, "gasPrice": 1000000000 })
    reject_transaction = proposal_contract.functions.reject().build_transaction({ "from": admin_account, "gas": 300000, "gasPrice": 1000000000 })

    order["contract_address"] = proposal_contract.address

    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        redis.lrem(Configuration.REDIS_ORDER_LIST, 1, matched_entry)
        redis.rpush(Configuration.REDIS_ORDER_LIST, json.dumps(order))

    return {
        "approve_transaction": { "to": approve_transaction["to"], "data": approve_transaction["data"] },
        "reject_transaction": { "to": reject_transaction["to"], "data": reject_transaction["data"] }
    }, 200

def normal_decision(order, matched_entry, approved):
    if approved is None:
        return { "message": "Field approved is missing." }, 400
    if not isinstance(approved, bool) :
        return { "message": "Invalid decision." }, 400

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

@director_blueprint.route("/decision", methods = ["POST"])
@role_check(Role.DIRECTOR)
def decision():
    body = request.get_json(silent=True)
    if body is None:
        return { "message": "Request body must be JSON." }, 400

    uuid = body.get("uuid", None)

    if uuid is None or not isinstance(uuid, str) or len(uuid) == 0:
        return { "message": "Field uuid is missing." }, 400

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

    if "voters" in body:
        return blockchain_decision(order, matched_entry, body.get("voters", None))
    else:
        return normal_decision(order, matched_entry, body.get("approved", None))

@director_blueprint.route("/report", methods = ["GET"])
@role_check(Role.DIRECTOR)
def report():
    pipeline = [
        { "$unwind": "$categories" },
        { "$group": {
            "_id": "$categories",
            "spent": { "$sum": "$buying_price" },
            "earned": { "$sum": { "$ifNull": ["$selling_price", 0] } }
        } },
        { "$project": { "_id": 0, "category": "$_id", "spent": 1, "earned": 1 } },
        { "$sort": { "earned": -1, "spent": 1, "category": 1 } }
    ]

    statistics = list(properties.aggregate(pipeline))

    return { "statistics": statistics }, 200
