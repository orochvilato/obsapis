from obsapis import app,use_cache,mdb,mdbrw,memcache
from flask import request,current_app,make_response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

@app.route('/logs')
def logs():
    resp = make_response(app.send_static_file('logs.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/logs2')
def logs2():
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'groupe':'$groupe'}
    pipeline = [{'$group':pgroup}]
    grps = []
    for g in mdb.logs.aggregate(pipeline):
        _g = g['_id']['groupe']
        if _g != None:
            grps.append((_g,g['n']))

    pgroup['_id'] = { 'depute':'$groupe'}

    grps = []
    for g in mdb.logs.aggregate(pipeline):
        _g = g['_id']['groupe']
        if _g != None:
            grps.append((_g,g['n']))

    return json_response(grps)

@app.route('/flushlogs')
def flushlogs():
    mdbrw.logs.remove()
    return "ok"

@app.route('/flushcache')
def flushcache():
    memcache.flush_all()
    return "ok"
