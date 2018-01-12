# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne

def update_amendements():
    ops = []
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteur'}
    pgroup['_id']['sort'] ='$sort'
    pipeline = [{'$match':{}},   {"$group": pgroup }] #'scrutin_typedetail':'amendement'

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
        #print d,stat
        ops.append(UpdateOne({'depute_shortid':d},{'$set':{'depute_amendements':stat}}))
    if ops:
        mdbrw.deputes.bulk_write(ops)
