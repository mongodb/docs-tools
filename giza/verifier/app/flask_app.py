from flask import Flask
import config
from pymongo import MongoClient

app = Flask(__name__)
app.config.from_object(config)

mongodb = MongoClient('localhost', app.config['MONGO_PORT'])
db = mongodb[app.config['MONGO_DBNAME']]

