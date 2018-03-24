# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne


def update_amendements():
    ops = []
    #return "ok"
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs.id'}
    pgroup['_id']['sort'] ='$sort'
    pipeline = [{'$match':{}},  {'$unwind':'$auteurs'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    stat_amdts = {}
    for amdt in mdb.amendements.aggregate(pipeline):
        amd = amdt['_id']
        if not amd['depute'] in stat_amdts.keys():
            stat_amdts[amd['depute']] = {'rediges':0,'adoptes':0,'cosignes':0}
        if amd['sort']==u'Adopté':
            stat_amdts[amd['depute']]['adoptes'] += amdt['n']
        stat_amdts[amd['depute']]['rediges'] += amdt['n']

    # TODO : stat GVT et commissions ?

    for d,stat in stat_amdts.iteritems():
        ops.append(UpdateOne({'depute_shortid':d},{'$set':{'depute_amendements':stat}}))
    if ops:
        mdbrw.deputes.bulk_write(ops)

from obsapis.controllers.admin.imports.amendements import get_signataires
def corrige_nonrenseignes():
    for amd in mdb.amendements.find({'$and':[{'sort':u'Non renseign\xe9'},{'_vu':{'$ne':True}}]}):
        meta = get_signataires(amd['urlAmend'])
        upd = {'_vu':True}
        if meta['SORT']!="":
            upd['sort'] = meta['SORT']
            #print amd['id'],meta['SORT']
            mdbrw.travaux.update_many({'idori':amd['id']},{'$set':{'sort':meta['SORT']}})
        mdbrw.amendements.update_one({'id':amd['id']},{'$set':upd})
