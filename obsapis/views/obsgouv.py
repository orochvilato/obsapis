from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function, strip_accents
import re
import random
import datetime
import pygal

from obsapis.config import cache_pages_delay
from obsapis.controllers.admin.imports.obsgouv import import_obsgouv_gdoc

@app.route('/obsgouv/get')
@cache_function(expires=120)
def obsgouv_getdata():
    return json_response(import_obsgouv_gdoc())
