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

@app.route('/svgs/hemicycle')
def hemicycle():
    depute = request.args.get('depute','')

    place = mdb.deputes.find_one({'depute_shortid':depute},{'depute_place':1})
    place = place.get('depute_place','') if place else ''
    place = request.args.get('place',place)

    groupe = request.args.get('groupe')
    base_url = request.args.get('baseurl','http://dev.observatoire-democratie.fr/assemblee/deputes')
    def genhemicycle():
        hrefs = {}
        titles = {}
        classes = {}

        for d in mdb.deputes.find({},{'depute_shortid':1,'_id':None,'depute_place':1,'depute_nom':1,'groupe_abrev':1}):
            plc = d['depute_place']
            hrefs[plc] = base_url+'/'+d['depute_shortid'] if 'base_url' else '#'
            titles[plc]= "place %s : %s (%s)" % (plc,d['depute_nom'],d['groupe_abrev'])
            classes[plc] = d['groupe_abrev']
        return render_template('svg/hemicycle-paths.svg',hrefs=hrefs,titles=titles,classes=classes)

    cachekey= u"hemicycle-paths"+base_url
    paths = use_cache(cachekey,lambda:genhemicycle(),expires=24*3600)

    return render_template('svg/hemicycle.svg',paths=paths,groupe=groupe,place='p'+(place or 'nope'))
