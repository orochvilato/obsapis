from obsapis import app,use_cache,mdb
from flask import request, Response
from obsapis.tools import json_response,cache_function,image_response
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel,genvisuelstat,genvisuelstat21,genvisuelstat21clean,maxis,getgauge,visuelvotecle

@app.route('/longs')
def longs():
    return json_response(maxis())


@app.route('/gauge')
def getgs():
    return Response(getgauge(), mimetype='image/png')

@app.route('/visuels/votecle/<int:num>')
def visvotcle(num):
    groupe=request.args.get('groupe',None)
    return image_response('png',visuelvotecle(num,groupe))


@app.route('/visuels/stat')
def genvisuel():
    depute = request.args.get('depute',None)
    stat = request.args.get('stat','participation')


    download = int(request.args.get('download','0'))
    v=genvisuelstat(depute,stat)
    headers = {'Cache-Control':'no-cache, no-store, must-revalidate','Pragma':'no-cache'}
    if download==0:
        r = Response(v, mimetype="image/png",headers=headers)
    else:
        headers.update({"Content-Disposition":
                     "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
        r = Response(v, mimetype="image/png",
                       headers=headers)
    return r


@app.route('/visuels/stat21')
def genvisuel21():
    depute = request.args.get('depute',None)
    stat = request.args.get('stat','participation')


    download = int(request.args.get('download','0'))
    if 'clean' in request.args:
        v=genvisuelstat21clean(depute,stat)
    else:
        v=genvisuelstat21(depute,stat)
    headers = {'Cache-Control':'no-cache, no-store, must-revalidate','Pragma':'no-cache'}
    if download==0:
        r = Response(v, mimetype="image/png",headers=headers)
    else:
        headers.update({"Content-Disposition":
                     "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
        r = Response(v, mimetype="image/png",
                       headers=headers)
    return r

@app.route('/visuels/<id>')
def apercu(id):
    depute = request.args.get('depute',None)
    download = int(request.args.get('download','0'))
    neutre = request.args.get('neutre')
    regen = request.args.get('regen')
    v=get_visuel(id,depute,regen=regen,neutre=neutre)
    if download==0:
        r = Response(v, mimetype="image/png")
    else:
        r = Response(v, mimetype="image/png",
                       headers={"Content-Disposition":
                                    "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
    return r

@app.route('/visuels/genall')
def genallvis():
    for d in list(mdb.deputes.find({'depute_actif':True},{'depute_shortid':1,'_id':None})):
        v=get_visuel('obs2',d['depute_shortid'])
    return "ok"
