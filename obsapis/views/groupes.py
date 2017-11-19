# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function, getdot
import re
import random
import datetime

from collections import OrderedDict
from obsapis.config import seuil_compat,cache_pages_delay

groupe_fields = ['groupe_libelle','groupe_compat','groupe_positions','groupe_nbmembres','groupe_abrev','groupe_declaration','groupe_membres','stats','groupe_nuages']
csp_liste = [(u"Cadres et professions intellectuelles sup\u00e9rieures",u"Cadres, Prof. Sup."), (u"Artisans, commer\u00e7ants et chefs d'entreprise",u"Artisants, Chefs d'entrep."), (u"Agriculteurs exploitants",u"Agriculteurs exploitants"),(u"Professions Interm\u00e9diaires",u"Professions Interm\u00e9diaires"),(u"Employ\u00e9s",u"Employ\u00e9s"),(u"Ouvriers",u"Ouvriers"),(u"Retrait\u00e9s",u"Retrait\u00e9s"),(u"Autres (y compris inconnu et sans profession d\u00e9clar\u00e9e)",u"Autres")]
classeage_liste = ["70-80 ans", "60-70 ans", "50-60 ans", "40-50 ans", "30-40 ans", "20-30 ans"]


@app.route('/groupes')
@app.route('/groupes/<func>')
@cache_function(expires=cache_pages_delay)
def groupes(func=""):
    abrev = func
    _fields = dict((f,1) for f in groupe_fields)
    _fields['_id']=None
    groupe = mdb.groupes.find_one({'groupe_abrev':abrev},_fields)
    if not groupe:
        groupe = mdb.groupes.find_one({'groupe_abrev':'FI'})


    president = [ m['uid'] for m in groupe['groupe_membres'] if m['actif']==True and m['qualite']==u'Président']
    president = mdb.deputes.find_one({'depute_uid':president[0]},{'_id':None,'depute_nom':1,'depute_shortid':1}) if president else None
    return json_response(dict(president = president,csp_liste=csp_liste,classeage_liste=classeage_liste,
                **groupe))
