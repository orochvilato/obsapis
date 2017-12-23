# -*- coding: utf-8 -*-
from obsapis import app,use_cache,mdb
from flask import request, Response, render_template
from obsapis.tools import json_response,cache_function,image_response
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel,genvisuelstat,genvisuelstat21,genvisuelstat21clean,maxis,getgauge,visuelvotecle

from obsapis.controllers.instantencommun import visueliec1
@app.route('/longs')
def longs():
    return json_response(maxis())


@app.route('/gauge')
def getgs():
    return Response(getgauge(), mimetype='image/png')

params = {'urgdem':{'titre':u'Urgence démocratique','couleur':'jaune'},
          'urgsoc':{'titre':u'Urgence sociale','couleur':'rouge'},
          'urgeco':{'titre':u'Urgence écologique','couleur':'vert'},
          'paixin':{'titre':u"La paix et l'international",'couleur':'violet'},
          'europe':{'titre':u"L'Europe en question",'couleur':'bleu'},
          'prohum':{'titre':u"Le progrès humain",'couleur':'orange' },
          'frohum':{'titre':u"frontières de l’humanité",'couleur':'orange'}
         }

@app.route('/visuels/iec_poc')
def view_ies_poc():
    contenu = u"""*2,5 millions* de français vivent dans un **désert médical**.

En *10 ans* le nombre de **médecins** généralistes a baissé de *8%* et cette **raréfaction** touche *93* départements.

Cela entraîne une *augmentation* du recours aux **Urgences**.
"""
    contenu = u"""*2,5 millions* de français ~vivent~ dans un **désert médical** :innocent:.

En *10 ans* le nombre de **médecins** :yum: généralistes a ~baissé~ de *8%* et cette **raréfaction** touche *93* départements.:poop: :sweat:

Cela :nerd: entraîne une :confused: *augmentation* du :slight_frown: recours aux **Urgences**.
"""
    theme=u"progrès humain"
    source=u"Observatoire de la Démocratie"
    return render_template('iec/proofofconcept.html',contenu=contenu,source=source,themes=params)

@app.route('/visuels/iec',methods=['POST'])
def view_visueliec():
    theme=request.form.get('theme')
    themecustom=request.form.get('themecustom')
    contenu=request.form.get('contenu')
    source=request.form.get('source')
    param = params[theme]
    return image_response('png',visueliec1(theme=theme,themecustom=themecustom, contenu=contenu,source=source,**param),filename=theme.replace(' ',''))

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
