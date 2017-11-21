from obsapis import app,use_cache,mdb
from flask import request, Response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel

@app.route('/visuel')
def visuel():
    depute = request.args.get('depute',None)
    neutre = int(request.args.get('neutre','1'))
    download = int(request.args.get('download','0'))
    v=get_visuel(depute,neutre)
    if download==0:
        r = Response(v, mimetype="image/png")
    else:
        r = Response(v, mimetype="image/png",
                       headers={"Content-Disposition":
                                    "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
    return r
