# -*- coding: utf-8 -*-

from obsapis import app,mdb
from flask import render_template
from bson import json_util

@app.route('/test')
def test():
    return json_util.dumps(mdb.scrutins.find_one({'scrutin_num':250}))
    return json_util.dumps(list(mdb.amendements.find({'sort':u"Adopt\u00e9","signataires_groupes":{'$elemMatch':{'$eq':'FI'}}},{'_id':None,'numInit':1,'numAmend':1})))


if __name__ == "__main__":
    app.run()
