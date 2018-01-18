# -*- coding: utf-8 -*-
from obsapis import mdbrw,mdb
from pymongo import UpdateOne

def normnom(nom):
    return " ".join([n[0].upper()+n[1:] for n in nom.lower().replace('   ',' ').replace('  ',' ').split(' ')])

def update_hatvp():
    from obsapis.scrapers import launchScript,getJson
    #launchScript('hatvp')
    collabs = getJson('hatvp')
    ids = [d['depute_shortid'] for d in mdb.deputes.find({},{'depute_shortid':1,'_id':None})]

    ops = []

    for dep,collabs in collabs.iteritems():
        collabs = [normnom(c) for c in collabs]
        ops.append(UpdateOne({'depute_shortid':dep},{'$set':{'depute_collaborateurs_hatvp':collabs}}))
    if ops:
        mdbrw.deputes.bulk_write(ops)
