from pymongo import MongoClient

from service.shared.configuration import Configuration

client = MongoClient(Configuration.MONGO_URI)
database = client.get_database("service")
properties = database.get_collection("properties")


class Property ( ):
    def __init__ ( self, name, categories, buying_price, buying_date, info, selling_price = None, selling_date = None ):
        self.name = name
        self.categories = categories
        self.buying_date = buying_date
        self.selling_date = selling_date
        self.buying_price = buying_price
        self.selling_price = selling_price
        self.info = info

    def to_document ( self ):
        return {
            "name": self.name,
            "categories": self.categories,
            "buying_date": self.buying_date,
            "selling_date": self.selling_date,
            "buying_price": self.buying_price,
            "selling_price": self.selling_price,
            "info": self.info
        }
