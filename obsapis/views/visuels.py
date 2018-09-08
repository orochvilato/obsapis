# -*- coding: utf-8 -*-
from obsapis import app,use_cache,mdb
from flask import request, Response, render_template
from obsapis.tools import json_response,cache_function,image_response, logitem
import re
import datetime

from obsapis.config import cache_pages_delay
#@cache_function(expires=cache_pages_delay)
from obsapis.controllers.visuels import get_visuel,genvisuelstat,genvisuelstat21,genvisuelstat21clean,maxis,getgauge,visuelvotecle, visuelvotecledetail, visuelvotecledetail21,visuelvotecledetail21big, visuelvotecledetailvideo
from obsapis.controllers.bingo import bingovisuel
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

@app.route('/visuels/liec')
def view_ies_poc():
    contenu = u"""*2,5 millions* de français vivent dans un **désert médical**.

En *10 ans* le nombre de **médecins** généralistes a baissé de *8%* et cette **raréfaction** touche *93* départements.

Cela entraîne une *augmentation* du recours aux **Urgences**.
"""
    contenu = u""":flag_mq|44: :loudspeaker|44: :fa-binoculars|44: *:fa-birthday-cake|44:*

Emoticons :ok_hand: + *FontAwesome :fa-fa:*.

:fa-angellist|125|#6bb592:
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


@app.route('/visuels/bingo')
def view_bingo():
    params = dict(
        margin_bottom = 60,
        margin_top = 684,
        margin_left = 170,
        border = 5,
        cols = 4,
        rows = 5,
        spacing = 25,
        fontsize = 50,
        inner_margin = 20,
        interline = 120,
        transparence_case = 200
        )
    mots = u"""CHIFFRES|D'OCCURENCE
MACRON A|ÉTÉ ÉLU;1
2022
HAINE DES|MÉDIAS (RSF)
SONDAGES
CASSEURS
ESSOUFLEMENT|DU MOUVEMENT
RUFFIN|VS JLM
BENOÎT|HAMON
ÉLECTIONS|EUROPÉENNES
DÉFAITE|DE L'OM
PARTIELS DES|ÉTUDIANTS;1
ÉLECTIONS|VÉNÉZUELA
UNION DE|LA GAUCHE
AGITATEUR;1
PRISE|D'OTAGE
APPEL À|LA VIOLENCE
MAIRIE DE|MARSEILLE
ISRAËL|SE DÉFEND
POUTINE"""
    order = ['margin_left','margin_top','margin_bottom','cols','rows','spacing','border','transparence_case','fontsize','inner_margin','interline']
    return render_template('bingo/bingo.html',params=[(k,params[k]) for k in order],mots=mots)


@app.route('/visuels/bingo',methods=['POST'])
def visbingo():
    #groupe=request.args.get('groupe',None)
    #font=int(request.args.get('fs','16'))
    #fontsub=int(request.args.get('fst','20'))
    return image_response('png',bingovisuel(request.form.to_dict()),filename="bingo.png")


@app.route('/visuels/votecle/<int:num>')
def visvotcle(num):
    groupe=request.args.get('groupe',None)
    font=int(request.args.get('fs','16'))
    fontsub=int(request.args.get('fst','20'))
    return image_response('png',visuelvotecle(num,groupe,font,fontsub))

@app.route('/visuels/votecledetail/<int:num>')
def visvotcledetail(num):
    font=int(request.args.get('fs','24'))
    fontsub=int(request.args.get('fst','30'))
    return image_response('png',visuelvotecledetail(num,font,fontsub))

@app.route('/visuels/votecledetail21/<int:num>')
def visvotcledetail21(num):
    font=int(request.args.get('fs','14'))
    fontsub=int(request.args.get('fst','16'))
    return image_response('png',visuelvotecledetail21(num,font,fontsub))

@app.route('/visuels/votecledetail21big/<int:num>')
def visvotcledetail21big(num):
    font=int(request.args.get('fs','14'))
    fontsub=int(request.args.get('fst','16'))
    return image_response('png',visuelvotecledetail21big(num,font,fontsub))

@app.route('/visuels/votecledetailvideo/<int:num>')
def visvotcledetailvideo(num):
    font=int(request.args.get('fs','20'))
    fontsub=int(request.args.get('fst','24'))
    return image_response('png',visuelvotecledetailvideo(num,font,fontsub))


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
@logitem(name='visuelstat',item=None,fields=['depute','stat'])
@cache_function(expires=600)
def genvisuel21():
    depute = request.args.get('depute',None)
    stat = request.args.get('stat','participation')



    if 'clean' in request.args:
        v=genvisuelstat21clean(depute,stat)
    else:
        v=genvisuelstat21(depute,stat)
    headers = {'Cache-Control':'no-cache, no-store, must-revalidate','Pragma':'no-cache'}
    if not 'download' in request.args:
        r = Response(v, mimetype="image/png",headers=headers)
    else:
        headers.update({"Content-Disposition":
                     "attachment;filename=obsdemocratie_%s_%s.png" % (depute,datetime.datetime.now().strftime('%Y_%m_%d'))})
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
