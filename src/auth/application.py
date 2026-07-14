from flask import Flask

from configuration import Configuration

application = Flask(__name__)
application.config.from_object(Configuration)

if (__name__ == "__main__"):
    application.run ( debug = True )

