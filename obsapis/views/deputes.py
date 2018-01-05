# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime

from collections import OrderedDict
from obsapis.config import seuil_compat,cache_pages_delay

tri_choices = OrderedDict([('stats.positions.exprimes',{'label':'Participation','classe':'deputes-participation','rank':'exprimes','precision':0,'unit':'%'}),
            ('stats.positions.dissidence',{'label':'Contre son groupe','classe':'deputes-dissidence','rank':'dissidence','precision':0,'unit':'%'}),
            ('stats.compat.FI',{'label':'Compatibilité FI','classe':'deputes-fi','rank':'compatFI','precision':0,'unit':'%'}),
            ('stats.compat.REM',{'label':'Compatibilité EM','classe':'deputes-em','rank':'compatREM','precision':0,'unit':'%'}),
            ('stats.nbitvs',{'label':"Nombre d'interventions",'classe':'deputes-interventions','rank':'nbitvs','precision':0,'unit':''}),
            ('stats.nbmots',{'label':"Nombre de mots",'classe':'deputes-mots','rank':'nbmots','precision':0,'unit':''}),
            ('stats.amendements.rediges',{'label':"Amendements rédigés",'classe':'deputes-mots','rank':'nbamendements','precision':0,'unit':''}),
            ('stats.amendements.adoptes',{'label':"Amendements adoptés (%)",'classe':'deputes-mots','rank':'pctamendements','precision':0,'unit':'%'}),
            ('stats.commissions.present',{'label':"Présence en commission",'classe':'deputes-mots','rank':'pctcommissions','precision':0,'unit':'%'}),

            ('stats.election.inscrits',{'label':"Voix en % des inscrits",'classe':'deputes-pctinscrits','precision':2,'rank':'pctinscrits','unit':'%'}),
            ('stats.election.exprimes',{'label':"Voix en % des votes exprimés",'classe':'deputes-pctexprimes','precision':2,'rank':'pctexprimes','unit':'%'}),
            ('stats.positions.absent',{'label':'','classe':'','precision':0,'rank':'absent','unit':'%'}),
            ('stats.positions.pour',{'label':'','classe':'','precision':0,'rank':'pour','unit':'%'}),
            ('stats.positions.contre',{'label':'','classe':'','precision':0,'rank':'contre','unit':'%'}),
            ('stats.positions.abstention',{'label':'','classe':'','precision':0,'rank':'abtention','unit':'%'}),
            ('depute_nom_tri',{'label':"Nom",'classe':'','rank':'N/A','unit':''})
            ])
tri_items = {'tops': ('stats.positions.exprimes','stats.positions.dissidence','stats.compat.FI','stats.compat.REM','stats.nbitvs','stats.nbmots','stats.amendements.rediges','stats.amendements.adoptes','stats.commissions.present','stats.election.exprimes','stats.election.inscrits'),
             'liste': ('depute_nom_tri','stats.positions.exprimes','stats.positions.dissidence','stats.compat.FI','stats.compat.REM')}


deputefields = ['depute_uid','depute_id','depute_shortid','depute_region','depute_departement','depute_departement_id',
                'depute_csp','groupe_qualite','depute_nom_sa','depute_vote_groupe_scrutin',
                'depute_circo','depute_nom','depute_contacts','groupe_abrev','groupe_libelle',
                'depute_election','depute_profession','depute_naissance','depute_suppleant',
                'depute_actif','depute_mandat_debut','depute_mandat_fin','depute_mandat_fin_cause',
                'depute_bureau','depute_mandats','depute_autresmandats','depute_collaborateurs',
                'depute_hatvp','depute_nuages','depute_place','stats']

deputesfields = ['depute_uid','depute_id','depute_shortid','depute_region','depute_departement','depute_departement_id','depute_nom_sa',
                 'depute_csp','depute_contacts','depute_suppleant','depute_bureau','depute_mandat_debut','depute_mandat_fin','depute_mandat_fin_cause',
                'depute_circo','depute_nom','groupe_abrev','groupe_libelle',
                'depute_profession','depute_naissance','depute_actif','depute_place','stats']
#deputesfields  = deputefields

#scrutins_by_id = cache.disk('scrutins_by_id',lambda: dict((s['scrutin_id'],s) for s in mdb.scrutins.find()), time_expire=3600)

deputesFI = use_cache('deputesfi',lambda:mdb.deputes.find({'groupe_abrev':'FI'}).distinct('depute_shortid'),expires=3600)

@app.route('/deputes/hasard')
def deputehasard():
    from obsapis.controllers.scrutins import getScrutinsCles
    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=3600)
    nbdeputes = use_cache('nbdeputes',lambda:mdb.deputes.find({'depute_actif':True}).count(),expires=3600)
    mfields = dict((f,1) for f in deputesfields)
    mfields.update({'_id':None})
    depute = mdb.deputes.find({'depute_actif':True},mfields).skip(int(random.random()*nbdeputes)).limit(1)[0]

    photo_an='http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg'
    depnumdep = depute['depute_departement_id'][1:] if depute['depute_departement_id'][0]=='0' else depute['depute_departement_id']
    if depute['depute_region']==depute['depute_departement']:
        depute_circo_complet = "%s (%s) / %se circ" % (depute['depute_departement'],depnumdep,depute['depute_circo'])
    else:
        depute_circo_complet = "%s / %s (%s) / %se circ" % (depute['depute_region'],depute['depute_departement'],depnumdep,depute['depute_circo'])

    resp = dict(depute_circo_complet = depute_circo_complet,
                depute_photo_an = photo_an,
                id = depute['depute_shortid'],
                **depute)

    return json_response(resp)


def deputeget(shortid):
    from obsapis.controllers.scrutins import getScrutinsCles
    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=36000)


    mfields = dict((f,1) for f in deputefields)
    mfields.update({'_id':None})
    depute = mdb.deputes.find_one({'depute_shortid':shortid},mfields)
    if not depute:
        depute = mdb.deputes.find_one({'depute_shortid':deputesFI[int(random.random()*len(deputesFI))]},mfields)
    else:
        pass
        #obsass_log('fiche',shortid)


    photo_an='http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+depute['depute_uid'][2:]+'.jpg'
    depnumdep = depute['depute_departement_id'][1:] if depute['depute_departement_id'][0]=='0' else depute['depute_departement_id']
    if depute['depute_region']==depute['depute_departement']:
        depute_circo_complet = "%s (%s) / %se circ" % (depute['depute_departement'],depnumdep,depute['depute_circo'])
    else:
        depute_circo_complet = "%s / %s (%s) / %se circ" % (depute['depute_region'],depute['depute_departement'],depnumdep,depute['depute_circo'])

    votes = list(mdb.votes.find({'depute_uid':depute['depute_uid']}).sort('scrutin_num',-1))
    votes_cles = list(mdb.votes.find({'depute_uid':depute['depute_uid'],'scrutin_num':{'$in':scrutins_cles.keys()}},{'scrutin_num':1,'vote_position':1,'scrutin_date':1,'scrutin_dossierLibelle':1}).sort('scrutin_num',-1))
    from collections import OrderedDict
    s_cles = OrderedDict()
    for v in votes_cles:
        v.update(scrutins_cles[v['scrutin_num']])
        if v['scrutin_dossierLibelle']=='N/A' and scrutins_cles[v['scrutin_num']]['dossier']:
            dossier = scrutins_cles[v['scrutin_num']]['dossier']
        else:
            dossier = v['scrutin_dossierLibelle']
        v['scrutin_dossierLibelle'] = dossier.replace(u'\u0092',"'")
        if not v['theme'] in s_cles:
            s_cles[v['theme']] = []
        s_cles[v['theme']].append(v)
    dates = {}
    weeks = {}
    for v in votes:
        pdat =  datetime.datetime.strptime(v['scrutin_date'],'%d/%m/%Y')
        wdat = pdat.strftime('%Y-S%W')
        sdat = pdat.strftime('%Y-%m-%d')
        if not wdat in weeks.keys():
            weeks[wdat] = {'e':0,'n':0}

        if not sdat in dates.keys():
            dates[sdat] = {'e':0,'n':0}
        weeks[wdat]['n']+= 1
        dates[sdat]['n']+= 1
        weeks[wdat]['e']+= 1 if v['vote_position']!='absent' else 0
        dates[sdat]['e']+= 1 if v['vote_position']!='absent' else 0


    resp = dict(dates=sorted([{"date": dat,"pct":round(float(v['e'])/v['n'],3)} for dat,v in dates.iteritems()],key=lambda x:x['date']),
                weeks=sorted([{"week": w,"pct":100*round(float(v['e'])/v['n'],2)} for w,v in weeks.iteritems()],key=lambda x:x['week']),
                votes_cles=s_cles,
                depute_circo_complet = depute_circo_complet,
                depute_photo_an = photo_an,
                id = depute['depute_shortid'],
                **depute)

    return resp





# ---------------------------------
# Page députés
# ---------------------------------

@app.route('/deputes')
@app.route('/deputes/<func>')
@logitem(name='deputes',item='func',fields=['tri','requete','region','ordre','age','groupe','csp','page','deputes'])
@cache_function(expires=cache_pages_delay)
def deputes(func=""):
    if func=='liste':
        resp = _ajax('liste')
    elif func=='top':
        resp = _ajax('top')
    else:
        resp = deputeget(func)

    return json_response(resp)


def _ajax(type_page):
    # ajouter des index (aux differentes collections)

    nb = int(request.args.get('itemsperpage','15'))
    age = request.args.get('age',None)
    csp = request.args.get('csp',None)
    page = int(request.args.get('page','1'))-1
    groupe = request.args.get('groupe',request.args.get('group',None))
    text = request.args.get('query',request.args.get('requete',''))

    region = request.args.get('region',None)
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
                  'stats.compat.FI':-1,
                  'stats.compat.REM':-1,
                  'stats.amendements.rediges':-1,
                  'stats.amendements.adoptes':-1,
                  'stats.commissions.present':-1,
                  'stats.positions.pour':-1,
                  'stats.positions.contre':-1,
                  'stats.positions.abstention':-1,
                  'stats.positions.absent':-1,
                  'stats.election.exprimes':-1,
                  'stats.election.inscrits':-1}

    filter = {'$and':[ {'depute_actif':(not 'ancien' in request.args)}]}

    if csp:
        filter['$and'].append({'depute_csp':csp})
    if age:
        filter['$and'].append({'depute_classeage':age})
    if groupe:
        filter['$and'].append({'groupe_abrev':groupe})
    if region:
        filter['$and'].append({'depute_region':region})
    if text:
        text = ''.join(c for c in text if not c in '[(])/\.*')
        utext = strip_accents(text)
        regx = re.compile(text, re.IGNORECASE)
        uregx = re.compile(utext, re.IGNORECASE)
        filter['$and'].append({'$or':[{'depute_nom':regx},{'depute_nom_sa':uregx}]})

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
    deputes_filters = dict((f,1) for f in deputesfields)
    deputes_filters['_id'] = False
    def countItems():
        rcount = mdb.deputes.find(filter,deputes_filters).sort(sort).count()
        skipped = 0

        if top:
            cfilter = {'$and':list(filter['$and'])}
            cfilter['$and'][-1] = {tri:{'$eq':None}}
            excount = mdb.deputes.find(cfilter).sort(sort).count()
            if excount>0 and 'stats.compat.' in tri:
                skipped=excount

        return {'totalitems':rcount, 'skipped':skipped, 'skippedpct':seuil_compat}
    cachekey= u"dep%s_%s_%s_%s_%s_%s" % (type_page,age,csp if csp else csp,groupe,text,region if region else region)
    #counts = use_cache(cachekey,lambda:countItems(),expires=3600)
    counts = countItems()
    #return json.dumps(counts)
    items = []

    for d in mdb.deputes.find(filter,deputes_filters).sort(sort).skip(skip).limit(nb):
        photo_an='http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+d['depute_uid'][2:]+'.jpg'
        depnumdep = d['depute_departement_id'][1:] if d['depute_departement_id'][0]=='0' else d['depute_departement_id']
        if d['depute_region']==d['depute_departement']:
            depute_circo_complet = "%s (%s) / %se circ" % (d['depute_departement'],depnumdep,d['depute_circo'])
        else:
            depute_circo_complet = "%s / %s (%s) / %se circ" % (d['depute_region'],d['depute_departement'],depnumdep,d['depute_circo'])
        d['depute_photo_an'] = photo_an
        d['depute_circo_complet'] = depute_circo_complet
        d['id'] = d['depute_shortid']
        if rank:
            d['depute_rank'] = getdot(d,rank)
        items.append(d)

    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(items),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=items,**counts)
    return result
