from obsapis import app,use_cache
from flask import request, Response, render_template
from obsapis.tools import json_response,cache_function,image_response
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuel.base.visuel2x1 import visuelmacaron,visuelclean

from obsapis.controllers.instantencommun import visueliec1


@app.route('/visuels/deputes/<stat>')
def visuel_deputes(stat):
    f = visuelmacaron if 'macaron' in request.args else visuelclean

    download = int(request.args.get('download','0'))

    if 'macaron' in request.args:
        f = visuelmacaron
        zone = dict(width=676,height=330,x=304,y=50,background="#fffdf1")
    else:
        f = visuelclean
        zone = dict(width=994,height=400,x=15,y=35,background="#fffdf1")
    if stat=='participation':
        from obsapis.controllers.visuel.charts.deputes.scrutins import participation_globale_par_tranche_de_10 as chart
        v = f([(chart(width=zone['width'],height=zone['height'],background=zone['background']),zone['x'],zone['y'])])
    elif stat=='commissions':
        from obsapis.controllers.visuel.charts.deputes.commissions import presence_globale_par_tranche_de_10 as chart
        v = f([(chart(width=zone['width'],height=zone['height'],background=zone['background']),zone['x'],zone['y'])])
    else:
        v = ""
    headers = {'Cache-Control':'no-cache, no-store, must-revalidate','Pragma':'no-cache'}
    if download==0:
        r = Response(v, mimetype="image/png",headers=headers)
    else:
        headers.update({"Content-Disposition":
                     "attachment;filename=%s-%s.png" % (depute,datetime.datetime.now().strftime('%Y-%m-%d'))})
        r = Response(v, mimetype="image/png",
                       headers=headers)
    return r
