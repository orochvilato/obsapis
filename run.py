# -*- coding: utf-8 -*-

from obsapis import app,mdb,mdbrw
from flask import render_template
from bson import json_util
import xmltodict
import requests
import re
from obsapis.tools import json_response
from obsapis.controllers.admin.imports.documents import importdocs
from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte
from obsapis.controllers.admin.updates.groupes import updateGroupesPresidents



@app.route('/updateScrutins')
def updScrutins():
    updateScrutinsTexte()
    return "ok"
@app.route('/ouv')
def ouv():
    depgp = dict((d['depute_shortid'],{'img':'http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+d['depute_uid'][2:]+'.jpg','g':d['groupe_abrev'],'n':d['depute_nom']}) for d in mdb.deputes.find({},{'depute_nom':1,'depute_uid':1,'depute_shortid':1,'groupe_abrev':1,'_id':None}))
    shortids = dict((d['depute_id'],d['depute_shortid']) for d in mdb.deputes.find({},{'depute_id':1,'depute_shortid':1,'_id':None}))
    depsig = {}
    for doc in mdb.documentsan.find({'signataires':{'$ne':None}},{'numero':1,'signataires':1,'_id':None}):
        if doc['signataires']:
            sig1 = doc['signataires'][0]
            if sig1:
                for sig in doc['signataires'][1:]:
                    if sig and depgp[sig1]['g']!=depgp[sig]['g'] and depgp[sig]['g']!='NI':
                        if sig=='mohamedlaqhila':
                            print doc

                        depsig[sig] = depsig.get(sig,0)+1

    for amd in mdb.amendements.find({},{'numAmend':1,'signataires_ids':1,'_id':None}):
        if not amd['signataires_ids']:
            continue
        sig1 = shortids.get(amd['signataires_ids'][0],None)
        if sig1:
            for sig in amd['signataires_ids'][1:]:
                sig2 = shortids[sig]
                if sig2 and depgp[sig1]['g']!=depgp[sig2]['g'] and depgp[sig2]!='NI':
                    if sig2=='mohamedlaqhila':
                        print amd
                    depsig[sig2] = depsig.get(sig2,0)+1

    return json_response(sorted(depsig.iteritems(),key=lambda x:x[1],reverse=True))

@app.route('/test')
def test():
    return json_util.dumps(updateGroupesPresidents())
    return json_util.dumps(mdb.groupes.find_one({},{'groupe_abrev':1,'stats':1}))
    return json_util.dumps(mdb.deputes.find_one({'depute_shortid':'thierrysolere'},{'stats':1,'_id':None}))
    return json_util.dumps(list(mdb.amendements.find({'numAmend':'311'})))
    return json_util.dumps([(d['depute_nom'],
                             d['stats']['positions']['exprimes'],
                             d['stats']['votesamdements']['pctpour'],
                             d['depute_shortid']) for d in mdb.deputes.find({'groupe_abrev':'REM','stats.positions.exprimes':{'$gt':20}},{'depute_nom':1,'depute_shortid':1,'stats.positions.exprimes':1,'stats.votesamdements.pctpour':1}).sort([('stats.votesamdements.pctpour',-1)]).limit(20)])
    from fuzzywuzzy import fuzz
    sdesc = [(s['scrutin_dossier'],s['scrutin_dossierLibelle'],s['scrutin_desc'][20:]) for s in mdb.scrutins.find({'scrutin_dossier':{'$ne':'N/A'}},{'scrutin_dossier':1,'scrutin_dossierLibelle':1,'scrutin_desc':1,'_id':None})]
    r = []
    for s in mdb.scrutins.find({'scrutin_dossier':'N/A'},{'scrutin_desc':1,'_id':None,'scrutin_id':1}):
        for dos,doslib,d in sdesc:
            fz = fuzz.partial_ratio(s['scrutin_desc'][20:],d)
            if fz>97:
                r.append((s['scrutin_id'],dos,doslib))
                break

    return json_util.dumps(r)
    return json_util.dumps([(d['depute_shortid'],d['depute_suppleant'],d['depute_mandat_fin']) for d in mdb.deputes.find({'depute_actif':False})])
    return json_util.dumps(list(mdb.amendements.find({'sort':u"Adopt\u00e9","signataires_groupes":{'$elemMatch':{'$eq':'FI'}}},{'_id':None,'numInit':1,'numAmend':1})))


if __name__ == "__main__":

    app.run(debug=True)
