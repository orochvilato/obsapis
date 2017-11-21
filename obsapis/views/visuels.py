from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel

@app.route('/visuel')
def visuel():
    
    return get_visuel('test')
