# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne

def update_stats_interventions():
    ops = []
    #return "ok"
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$depute_shortid','rapporteur':'$itv_rapporteur'}
    pipeline = [{'$match':{'$and':[{'itv_ctx_n':1},{'itv_president':False}]}},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'
    return list(mdb.interventions.aggregate(pipeline))
