# -*- coding: utf-8 -*-

from obsapis import app,mdb
from flask import render_template
from bson import json_util

@app.route('/test')
def test():
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
