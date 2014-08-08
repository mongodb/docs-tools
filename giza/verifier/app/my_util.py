import simplejson
from bson import json_util
import os
import logging

logger = logging.getLogger('my_util')
logging.basicConfig(level=logging.DEBUG)

def load_json(file_name, db):
    file_no_ext = os.path.basename(file_name)
    file_no_ext = os.path.splitext(file_no_ext)[0]
    with open(file_name,"r") as file:
        json_data = file.read()
        data = simplejson.loads(json_data, object_hook=json_util.object_hook)
        for d in data[file_no_ext]:
            db[file_no_ext].insert(d)
        
