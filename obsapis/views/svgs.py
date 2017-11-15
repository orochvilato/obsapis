from obsapis import app,use_cache,mdb
from flask import request,render_template,make_response,Response
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay




@app.route('/svgs/circonscription')
@cache_function(expires=cache_pages_delay*100)
def svgcirco():
    circo = request.args.get('id',None)
    if not circo:
        depute=request.args.get('depute',None)
        if depute:
            circo = mdb.deputes.find_one({'depute_shortid':depute},{'depute_circo_id':1,'_id':None}).get('depute_circo_id',None)

    circosel = mdb.circonscriptions.find_one({'id':circo}) if circo else None
    if not circo and not circosel:
        return ""
    dep = circo.split('-')[0]

    if not circosel:
        return render_template('svg/circoworld.svg',dep=dep,circo=circo)
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
    #return json_response(circos)
    datasvg = render_template('svg/circofrance.svg',dep=dep,circo=circosel,circos=circos,strokewidth=float(max(circosel['w'],circosel['h']))*0.0136)
    return datasvg
    response= make_response(datasvg)
    response.headers["Content-Type"] = "image/svg+xml"
    return response

def hemicycle(place="nope",groupe="",base_url=""):
    return XML(response.render('svg/hemicyclelight.svg',place='p'+(place or 'nope'),groupe=groupe,base_url='/'+base_url))
