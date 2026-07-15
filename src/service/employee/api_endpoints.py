import json
import uuid
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, request
from redis import Redis

from shared.credential_decorators import role_check;
from auth.models import Role
from service.shared.configuration import Configuration
from service.shared.models import properties

employee_blueprint = Blueprint("employee", __name__)

VALID_OPERATORS = { "eq", "ne", "gt", "gte", "lt", "lte", "in", "nin" }

@employee_blueprint.route("/search", methods = ["POST"])
@role_check(Role.EMPLOYEE)
def search():
    body = request.get_json(silent=True)
    if body is None:
        name = None
        category = None
        buying_date = None
        selling_date = None
        info_filters = None
    else:
        name = body.get("name", None)
        category = body.get("category", None)
        buying_date = body.get("buying_date", None)
        selling_date = body.get("selling_date", None)
        info_filters = body.get("info_filters", None)

    if name is not None and len(name) > 256:
        return { "message": "Name must be at most 256 characters." }, 400
    if category is not None and len(category) > 256:
        return { "message": "Category must be at most 256 characters." }, 400

    if buying_date is not None:
        try:
            buying_date = datetime.fromisoformat(buying_date)
        except ValueError:
            return { "message": "Buying date must be in ISO 8601 format." }, 400
    if selling_date is not None:
        try:
            selling_date = datetime.fromisoformat(selling_date)
        except ValueError:
            return { "message": "Selling date must be in ISO 8601 format." }, 400

    if info_filters is not None:
        if not isinstance(info_filters, list):
            return { "message": "Info filters must be a list." }, 400
        for info_filter in info_filters:
            if not isinstance(info_filter, dict) or set(info_filter.keys()) != {"field", "operator", "value"}:
                return { "message": "Each info filter must have exactly field, operator and value." }, 400
            if not isinstance(info_filter["field"], str) or info_filter["field"] == "":
                return { "message": "Info filter field must be a non-empty string." }, 400
            if info_filter["operator"] not in VALID_OPERATORS:
                return { "message": "Info filter operator must be a valid MongoDB operator." }, 400

    conditions = []

    if name is not None:
        conditions.append({ "name": { "$regex": name, "$options": "i" } })
    if category is not None:
        conditions.append({ "categories": category })
    if buying_date is not None:
        conditions.append({ "buying_date": { "$gte": buying_date } })
    if selling_date is not None:
        conditions.append({ "selling_date": { "$lte": selling_date } })
    if info_filters is not None:
        for info_filter in info_filters:
            conditions.append({ f"info.{info_filter['field']}": { f"${info_filter['operator']}": info_filter["value"] } })

    query = { "$and": conditions } if len(conditions) > 0 else {}

    results = list(properties.find(query))
    for result in results:
        result["id"] = str(result.pop("_id"))
        result["buying_date"] = result["buying_date"].isoformat()
        if result.get("selling_price") is None:
            result.pop("selling_price", None)
            result.pop("selling_date", None)
        else:
            result["selling_date"] = result["selling_date"].isoformat()

    return { "assets": results }, 200

@employee_blueprint.route("/create_buy_order", methods = ["POST"])
@role_check(Role.EMPLOYEE)
def create_buy_order():
    body = request.get_json(silent=True)
    if body is None:
        return { "message": "Request body must be JSON." }, 400

    name = body.get("name", None)
    categories = body.get("categories", None)
    buying_price = body.get("buying_price", None)
    info = body.get("info", None)

    if name is None or isinstance(name, str) and len(name) == 0:
        return { "message": "Field name is missing." }, 400
    if categories is None:
        return { "message": "Field categories is missing." }, 400
    if buying_price is None:
        return { "message": "Field buying_price is missing." }, 400
    if info is None:
        return { "message": "Field info is missing." }, 400
    
    if not isinstance(name, str):
        return { "message": "Name must be string." }, 400
    if not isinstance(categories, list) or not all(isinstance(c, str) for c in categories):
        return { "message": "Categories must be list of strings." }, 400
    if not isinstance(buying_price, int):
        return { "message": "Invalid buying price." }, 400
    if not isinstance(info, object):
        return { "message": "Info must be an object" }, 400
    
    if len(name) > 256:
        return { "message": "Name must be at most 256 characters." }, 400
    if len(categories) == 0:
        return { "message": "Categories list is empty." }, 400
    if buying_price <= 0:
        return { "message": "Invalid buying price." }, 400
    
    to_save = {
        "uuid": str(uuid.uuid4()),
        "order_type": "BUY",
        "name": name,
        "categories": categories,
        "buying_price": buying_price,
        "info": info,
    }

    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        redis.rpush(Configuration.REDIS_ORDER_LIST, json.dumps(to_save))

    return {}, 200

@employee_blueprint.route("/create_sell_order", methods = ["POST"])
@role_check(Role.EMPLOYEE)
def create_sell_order():
    body = request.get_json(silent=True)
    if body is None:
        return { "message": "Request body must be JSON." }, 400

    id = body.get("id", None)
    selling_price = body.get("selling_price", None)

    if id is None or isinstance(id, str) and len(id) == 0:
        return { "message": "Field id is missing." }, 400
    if selling_price is None:
        return { "message": "Field selling_price is missing." }, 400
    
    if not isinstance(selling_price, int) or selling_price <= 0:
        return { "message": "Invalid selling price." }, 400

    try:
        object_id = ObjectId(id)
    except InvalidId:
        return { "message": "Invalid id." }, 400

    obj = list(properties.find({ "_id": object_id }))
    if len(obj) == 0:
        return { "message": "Invalid id." }, 400
    
    to_save = {
        "uuid": str(uuid.uuid4()),
        "order_type": "SELL",
        "id": id,
        "selling_price": selling_price,
    }
    
    with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
        redis.rpush(Configuration.REDIS_ORDER_LIST, json.dumps(to_save))

    return {}, 200