from obsapis import app,use_cache,mdb
from flask import request,current_app,Response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

@app.route('/logs')
def logs():
    resp = Response(open('obsapis/static/logs.html').read())
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp
