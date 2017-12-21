# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime

from collections import OrderedDict
from obsapis.config import seuil_compat,cache_pages_delay


groupe_fields = ['president','groupe_libelle','groupe_compat','groupe_positions','groupe_nbmembres','groupe_abrev','groupe_declaration','groupe_membres','stats','groupe_nuages']
groupes_fields = ['president','groupe_libelle','groupe_nbmembres','groupe_abrev','stats','depute_hasard']

csp_liste = [(u"Cadres et professions intellectuelles sup\u00e9rieures",u"Cadres, Prof. Sup."), (u"Artisans, commer\u00e7ants et chefs d'entreprise",u"Artisants, Chefs d'entrep."), (u"Agriculteurs exploitants",u"Agriculteurs exploitants"),(u"Professions Interm\u00e9diaires",u"Professions Interm\u00e9diaires"),(u"Employ\u00e9s",u"Employ\u00e9s"),(u"Ouvriers",u"Ouvriers"),(u"Retrait\u00e9s",u"Retrait\u00e9s"),(u"Autres (y compris inconnu et sans profession d\u00e9clar\u00e9e)",u"Autres")]
classeage_liste = ["70-80 ans", "60-70 ans", "50-60 ans", "40-50 ans", "30-40 ans", "20-30 ans"]

tri_choices = OrderedDict([('stats.positions.exprimes',{'label':'Participation','classe':'deputes-participation','rank':'exprimes','precision':0,'unit':'%'}),
            ('stats.positions.dissidence',{'label':'Contre son groupe','classe':'deputes-dissidence','rank':'dissidence','precision':0,'unit':'%'}),
            ('stats.nbitvs',{'label':"Nombre d'interventions",'classe':'deputes-interventions','rank':'nbitvs','precision':0,'unit':''}),
            ('stats.nbmots',{'label':"Nombre de mots",'classe':'deputes-mots','rank':'nbmots','precision':0,'unit':''}),
            ('stats.nbitvs_depute',{'label':"Nombre d'interventions",'classe':'deputes-interventions','rank':'nbitvs_depute','precision':0,'unit':''}),
            ('stats.nbmots_depute',{'label':"Nombre de mots",'classe':'deputes-mots','rank':'nbmots_depute','precision':0,'unit':''}),
            ('stats.amendements.rediges',{'label':"Amendements rédigés",'classe':'deputes-mots','rank':'nbamendements','precision':0,'unit':''}),
            ('stats.amendements.rediges_depute',{'label':"Amendements rédigés",'classe':'deputes-mots','rank':'nbamendements_depute','precision':0,'unit':''}),
            ('stats.amendements.adoptes',{'label':"Amendements adoptés (%)",'classe':'deputes-mots','rank':'pctamendements','precision':0,'unit':'%'}),
            ('stats.commissions.toutes.present',{'label':"Présence en commission",'classe':'deputes-mots','rank':'pctcommissions','precision':0,'unit':'%'}),
            ('stats.positions.absent',{'label':'','classe':'','precision':0,'rank':'absent','unit':'%'}),
            ('stats.positions.pour',{'label':'','classe':'','precision':0,'rank':'pour','unit':'%'}),
            ('stats.positions.contre',{'label':'','classe':'','precision':0,'rank':'contre','unit':'%'}),
            ('stats.positions.abstention',{'label':'','classe':'','precision':0,'rank':'abtention','unit':'%'}),
            ])

def groupeget(abrev):
    _fields = dict((f,1) for f in groupe_fields)
    _fields['_id']=None
    groupe = mdb.groupes.find_one({'groupe_abrev':abrev},_fields)
    if not groupe:
        groupe = mdb.groupes.find_one({'groupe_abrev':'FI'})


    return dict(csp_liste=csp_liste,classeage_liste=classeage_liste,
                **groupe)

@app.route('/groupes')
@app.route('/groupes/<func>')
@logitem(name='groupes',item='func',fields=['tri','requete','ordre','groupes'])
@cache_function(expires=0)
def groupes(func=""):
    if func=='liste':
        resp = _ajax('liste')
    elif func=='top':
        resp = _ajax('top')
    else:
        resp = groupeget(func)

    return json_response(resp)



def _ajax(type_page):
    # ajouter des index (aux differentes collections)

    nb = int(request.args.get('itemsperpage','15'))
    page = int(request.args.get('page','1'))-1
    text = request.args.get('query',request.args.get('requete',''))

    top = None if type_page=='liste' else type_page
    tri = request.args.get('tri',request.args.get('sort','stats.positions.exprimes' if top else 'stats.hasard'))
    direction = request.args.get('ordre',request.args.get('order','down' if top else 'up'))
    if direction =='asc':
        direction = 'up'
    elif direction =='desc':
        direction = 'down'

    tops_dir = {'stats.positions.exprimes':-1,
                  'stats.positions.dissidence':-1,
                  'stats.nbitvs':-1,
                  'stats.nbmots':-1,
                  'stats.nbitvs_depute':-1,
                  'stats.nbmots_depute':-1,
                  'stats.compat.FI':-1,
                  'stats.compat.REM':-1,
                  'stats.amendements.rediges':-1,
                  'stats.amendements.rediges_depute':-1,
                  'stats.amendements.adoptes':-1,
                  'stats.commissions.toutes.present':-1,
                  'stats.positions.pour':-1,
                  'stats.positions.contre':-1,
                  'stats.positions.abstention':-1,
                  'stats.positions.absent':-1,
                  'stats.election.exprimes':-1,
                  'stats.election.inscrits':-1}

    filter = {'$and':[ {'groupe_abrev':{'$nin':['NI','LC']}}]}

    if text:
        text = ''.join(c for c in text if not c in '[(])/\.*')
        utext = strip_accents(text)
        regx = re.compile(text, re.IGNORECASE)
        uregx = re.compile(utext, re.IGNORECASE)
        filter['$and'].append({'$or':[{'groupe_libelle':regx},{'groupe_libelle_sa':uregx}]})

    sort = []
    rank = None
    if top:
        #direction = tops_dir[tri] * (1 if top=='top' else -1)
        #rank = 'stats.ranks.'+('down' if (tops_dir[tri]==-1 and top=='top') else 'up')+'.'+tri_choices[tri]['rank']
        rank = 'stats.ranks.'+direction+'.'+tri_choices[tri]['rank']
        #sort += [ ('stats.nonclasse',1),(tri,direction),(rank,tops_dir[tri]*(-1 if top=='top' else 1))]
        sort += [ ('stats.nonclasse',1),(rank,1)]
        filter['$and'].append({tri:{'$ne':None}})
        #filter['$and'].append({tri:{'$ne':'N/A'}})
    else:
        sort += [ (tri,1 if direction=='up' else -1)]

    skip = nb*page
    groupes_filters = dict((f,1) for f in groupes_fields)
    groupes_filters['_id'] = False
    def countItems():
        rcount = mdb.groupes.find(filter,groupes_filters).sort(sort).count()
        skipped = 0

        if top:
            cfilter = {'$and':list(filter['$and'])}
            cfilter['$and'][-1] = {tri:{'$eq':None}}
            excount = mdb.groupes.find(cfilter).sort(sort).count()
            if excount>0 and 'stats.compat.' in tri:
                skipped=excount

        return {'totalitems':rcount, 'skipped':skipped, 'skippedpct':seuil_compat}
    cachekey= u"gp%s_%s" % (type_page,text)
    #counts = use_cache(cachekey,lambda:countItems(),expires=3600)
    counts = countItems()
    #return json.dumps(counts)
    items = []

    for g in mdb.groupes.find(filter,groupes_filters).sort(sort).skip(skip).limit(nb):
        g['id'] = g['groupe_abrev']
        if rank:
            g['groupe_rank'] = getdot(g,rank)
        items.append(g)


    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(items),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=items,**counts)
    return result
