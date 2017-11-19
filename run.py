# -*- coding: utf-8 -*-

from obsapis import app,mdb
from flask import render_template
from bson import json_util

@app.route('/test')
def test():

    
    return json_util.dumps([(d['depute_shortid'],d['depute_suppleant'],d['depute_mandat_fin']) for d in mdb.deputes.find({'depute_actif':False})])
    return json_util.dumps(list(mdb.amendements.find({'sort':u"Adopt\u00e9","signataires_groupes":{'$elemMatch':{'$eq':'FI'}}},{'_id':None,'numInit':1,'numAmend':1})))


if __name__ == "__main__":
    app.run()
