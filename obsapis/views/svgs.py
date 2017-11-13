from obsapis import app,use_cache,mdb
from flask import request,render_template
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay



@cache_function(expires=cache_pages_delay)
@app.route('/svgs/circonscription/<id>')
def svgcirco(id):
    if not id:
        circo = '013-01'
    else:
        circo = id
    dep = circo.split('-')[0]
    circosel = mdb.circonscriptions.find_one({'id':circo})
    if not circosel:
        return XML(response.render('svg/circoworld.svg',dep=dep,circo=circo))
    if circosel['paris']:
        filtre = {'paris':True}
    else:
        filtre = {'dep':dep}
    circos = {}
    stroke ='light' if circosel['paris'] or circosel['ville'] else 'normal'
    for c in mdb.circonscriptions.find(filtre):
        c['strokewidth'] = float(max(c['w'],c['h']))
        if not c['ville'] and c['id'][0:3]!=dep:
            c['class'] = "autres stroke"+stroke
            g = 'france'
        elif not c['ville'] and c['id'][0:3]==dep:
            c['class']="circo stroke"+stroke
            g = dep
        elif c['ville']:
            c['class']="circo "+('inville' if circosel['ville'] else 'outville')+" stroke"+stroke
            g = 'ville'
            c['villeitem'] = 'ville="1"' if circosel['ville'] else ''

        if not g in circos.keys():
            circos[g] = []
        circos[g].append(c)
    return json_response(circos)
    return render_template('svg/circofrance.svg',dep=dep,circo=circosel,circos=circos,strokewidth=float(max(circosel['w'],circosel['h']))*0.0136)
    return XML(response.render('svg/circofrance.svg',dep=dep,circo=circosel,circos=circos))

def hemicycle(place="nope",groupe="",base_url=""):
    return XML(response.render('svg/hemicyclelight.svg',place='p'+(place or 'nope'),groupe=groupe,base_url='/'+base_url))
