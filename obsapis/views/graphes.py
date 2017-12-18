# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request, render_template
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal
import math
from obsapis.config import cache_pages_delay

from obsapis.controllers.admin.imports.documents import importdocs
from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte

from collections import Counter


@app.route('/graphes/connections')
def connectionsdeputes():
    return render_template('graphes/connexions2.html')

@app.route('/graphes/connections.json')
@cache_function(expires=1200)
def connectionsjson():
    gsel = [0,4,5,7]
    gps = {'FI':0,'REM':1,'MODEM':2,'LR':3,'GDR':4,'NG':5,'NI':6,'UAI':7}
    counts = {}
    depgp = dict((d['depute_shortid'],{'img':'http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+d['depute_uid'][2:]+'.jpg','gn':d['groupe_abrev'],'g':gps[d['groupe_abrev']],'n':d['depute_nom']}) for d in mdb.deputes.find({},{'depute_nom':1,'depute_uid':1,'depute_shortid':1,'groupe_abrev':1,'_id':None}))
    shortids = dict((d['depute_id'],d['depute_shortid']) for d in mdb.deputes.find({},{'depute_id':1,'depute_shortid':1,'_id':None}))
    liens = []
    allitems = []
    for doc in mdb.documentsan.find({'signataires':{'$ne':None}},{'numero':1,'signataires':1,'_id':None}):
        if doc['signataires']:
            sig1 = doc['signataires'][0]
            counts[sig1] = counts.get(sig1,[])
            if sig1 and depgp[sig1]['g'] in gsel:
                for sig in doc['signataires'][1:]:
                    if sig:
                        counts[sig] = counts.get(sig,[])
                        if depgp[sig1]['g'] in gsel:
                            if depgp[sig1]['g']!=depgp[sig]['g']:
                                counts[sig1].append(sig)
                                counts[sig].append(sig1)
                            allitems.append(sig)
                            liens.append((sig1,sig))
                if len(counts[sig1])>0:
                    allitems.append(sig1)

    for amd in mdb.amendements.find({},{'signataires_ids':1,'_id':None}):
        if not amd['signataires_ids']:
            continue
        sig1 = shortids.get(amd['signataires_ids'][0],None)
        counts[sig1] = counts.get(sig1,[])
        if sig1 and depgp[sig1]['g'] in gsel:
            for sig in amd['signataires_ids'][1:]:
                sig2 = shortids[sig]
                if sig2:
                    counts[sig2] = counts.get(sig2,[])
                    if depgp[sig1]['g'] in gsel:
                        if depgp[sig1]['g']!=depgp[sig2]['g']:
                            counts[sig1].append(sig2)
                            counts[sig2].append(sig1)
                        allitems.append(sig2)
                        liens.append((sig1,sig2))

            if len(counts[sig1])>0:
                allitems.append(sig1)


    r = {'nodes':[],'links':[]}
    c = Counter(frozenset(x) for x in liens).items()
    mx = max([x[1] for x in c])


    counts = dict((c,len(list(set(v)))) for c,v in counts.iteritems())
    allitems = list(set([it for it in allitems if counts[it]>0]))
    for i,d in enumerate(allitems):
        r['nodes'].append({'img':depgp[d]['img'],'id':d,'name':"%s (%s)" % (depgp[d]['n'],depgp[d]['gn']),'group':depgp[d]['g'],'count':counts.get(d,0)})

    for l,n in Counter(frozenset(x) for x in liens).items():
        if len(list(l))==2 :
            s,t = list(l)
            if (depgp[s]['g'] in gsel or depgp[t]['g'] in gsel) and s in allitems and t in allitems:
                r['links'].append({'source':s,'target':t,'value':n})




    return json_response(r)

#@app.route('/charts/participationgroupes')
#def votesgroupes():
