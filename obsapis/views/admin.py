# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

from obsapis.config import cache_pages_delay

#@app.route('/charts/participationgroupes')
#def votesgroupes():
