
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
import pymongo
from bson import json_util

from config_private import mongo_read_user,mongo_read_password

client = pymongo.MongoClient('mongodb://%s:%s@observatoire-assemblee.orvdev.fr:27017/obsass' %(mongo_read_user,mongo_read_password))
mdb = client.obsass

from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

import bmemcached
memcache = bmemcached.Client(('observatoire-assemblee.orvdev.fr:11211',))



def use_cache(k,fct,expires=60):
    k = k.encode('utf8')
    if expires==0:
        memcache.delete(k)
        v=None
    else:
        v = memcache.get(k)
    if not v:
        v = fct()
        if expires!=0:
            memcache.set(k,v,time=expires)
    else:
        pass
    return v

from views import deputes,votes,interventions,svgs,logs
