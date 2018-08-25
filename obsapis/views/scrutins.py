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
        if s['scrutin_dossierLibelle']=='N/A' and scrutins_cles[s['scrutin_num']]['dossier']:
            dossier = scrutins_cles[s['scrutin_num']]['dossier']
        else:
            dossier = s['scrutin_dossierLibelle']
        positions = dict(scrutins_positions[s['scrutin_num']])
        if scrutins_cles[s['scrutin_num']]['inversion'] == 'oui':

            positions['position'] = {'pour':'contre','contre':'pour'}.get(positions['position'],positions['position'])

            positions['pour'] = scrutins_positions[s['scrutin_num']]['contre']
            positions['contre'] = scrutins_positions[s['scrutin_num']]['pour']

        scles.append(dict(desc=s['scrutin_desc'],date=s['scrutin_date'],
                          sort=s['scrutin_sort'],dossierLibelle=dossier.replace(u'\u0092',"'"),
                          detail=scrutins_cles[s['scrutin_num']],positions=positions))
    return json_response(scles)

#@cache_function(expires=cache_pages_delay)
@app.route('/scrutins/detail/<int:num>')
def scrutinsdetail(num):
    scrutin = mdb.scrutins.find_one({'scrutin_num':num})
    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=3600)
    scrutin.update(scrutins_cles.get(num,{}))
    positions = {}
    for dpos in mdb.votes.find({'scrutin_num':num},{'depute_shortid':1,'groupe_abrev':1,'vote_position':1}):
        depid = dpos['depute_shortid']
        gp = dpos['groupe_abrev']
        pos = dpos['vote_position']
        if not pos in positions.keys():
            positions[pos] = {}
        if not gp in positions[pos].keys():
            positions[pos][gp] = []
        positions[pos][gp].append(depid)

    scrutin['positions'] = positions
    return json_response(scrutin)
