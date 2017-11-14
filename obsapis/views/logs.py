from obsapis import app,use_cache,mdb
from flask import request,current_app,response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

@app.route('/logs')
def logs():
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return current_app.send_static_file('logs.html')
