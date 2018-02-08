from obsapis import app,use_cache,mdb,mdbrw,memcache, obspath
from flask import request,current_app,make_response, render_template,Response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

@app.route('/logs')
def logs():
    resp = Response(open(obspath+'/obsapis/static/logs.html','r').read())
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/logs100')
def logs50():
    resp = Response(open(obspath+'/obsapis/static/logs100.html','r').read())
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp


@app.route('/logs2')
def logs2():
    #return json_response(mdb.logs.find_one())
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'groupe':'$groupe'}
    pipeline = [{'$group':pgroup}]
    grps = []
    for g in mdb.logs.aggregate(pipeline):
        _g = g['_id']['groupe']
        if _g != None:
            grps.append((_g,g['n']))

    pgroup['_id'] = { 'item':'$item'}

    deps = []
    listetop= []
    for i in mdb.logs.aggregate(pipeline):
        _i = i['_id']['item']
        if _i in ['liste','top']:
            listetop.append((_i,i['n']))
        else:
            deps.append((_i,i['n']))

    pgroup['_id'] = { 'tri':'$tri'}

    tri = []
    for t in mdb.logs.aggregate(pipeline):
        _t = t['_id']['tri']
        if _t != None:
            tri.append((_t,t['n']))


    grps.sort(key=lambda x:x[1],reverse=True)
    deps.sort(key=lambda x:x[1],reverse=True)
    tri.sort(key=lambda x:x[1],reverse=True)
    listetop.sort(key=lambda x:x[1],reverse=True)
    return render_template('logs2.html',grps=grps,deps=deps,lstp=listetop,tri=tri)

@app.route('/flushlogs_nope')
def flushlogs():
    mdbrw.logs.remove()
    return "ok"

@app.route('/flushcache')
def flushcache():
    memcache.flush_all()
    return "ok"
