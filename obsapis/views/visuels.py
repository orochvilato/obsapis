from obsapis import app,use_cache,mdb
from flask import request, Response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel

@app.route('/visuels/<id>')
def visuel(id):
    depute = request.args.get('depute',None)
    download = int(request.args.get('download','0'))
    v=get_visuel(id,depute)
    if download==0:
        r = Response(v, mimetype="image/png")
    else:
        r = Response(v, mimetype="image/png",
                       headers={"Content-Disposition":
                                    "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
    return r

@app.route('/visuels/genall')
def genallvis():
    for d in list(mdb.deputes.find({'depute_actif':True},{'depute_shortid':1,'_id':None}))[:10]:
        v=get_visuel('obs2',d['depute_shortid'])
    return "ok"
