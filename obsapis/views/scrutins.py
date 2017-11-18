# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function, getdot
import re
import random
import datetime

from obsapis.controllers.scrutins import getScrutinsCles,getScrutinsPositions

from collections import OrderedDict
from obsapis.config import seuil_compat,cache_pages_delay

@app.route('/scrutins/cles')
def scrutinscles():
    nb = int(request.args.get('nb','0'))
    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=3600)
    scrutins_positions = use_cache('scrutins_positions',lambda:getScrutinsPositions(),expires=36000)
    scrutins = mdb.scrutins.find({'scrutin_num':{'$in':scrutins_cles.keys()}}).sort([('scrutin_num',-1)])
    if nb>0:
        scrutins = scrutins.limit(nb)
    scles = []
    for s in scrutins:
        scles.append(dict(desc=s['scrutin_desc'],date=s['scrutin_date'],
                          sort=s['scrutin_sort'],
                          detail=scrutins_cles[s['scrutin_num']],positions=scrutins_positions[s['scrutin_num']]))
    return json_response(scles)
