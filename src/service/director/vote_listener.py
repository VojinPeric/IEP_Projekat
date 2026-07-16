import json
import time
from datetime import datetime, timezone

from bson import ObjectId
from redis import Redis

from service.shared.configuration import Configuration
from service.shared.models import Property, properties
from service.shared.blockchain import CONTRACT_ABI, web3

POLL_INTERVAL_SECONDS = 2

def resolve_order(redis, entry, order):
    contract = web3.eth.contract(address = order["contract_address"], abi = CONTRACT_ABI)

    votes_for = contract.functions.votesFor().call()
    votes_against = contract.functions.votesAgainst().call()
    majority = contract.functions.votersCount().call() // 2 + 1

    if votes_for >= majority:
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
        redis.lrem(Configuration.REDIS_ORDER_LIST, 1, entry)
    elif votes_against >= majority:
        redis.lrem(Configuration.REDIS_ORDER_LIST, 1, entry)

def run():
    while True:
        with Redis(host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT) as redis:
            entries = redis.lrange(Configuration.REDIS_ORDER_LIST, 0, -1)

            for entry in entries:
                order = json.loads(entry)
                if "contract_address" in order:
                    resolve_order(redis, entry, order)

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()
