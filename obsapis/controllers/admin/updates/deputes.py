# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne

from obsapis.controllers.admin.imports.contactsan import import_contactsan_gdoc
def updateDeputesContacts():
    contacts = import_contactsan_gdoc()
    ops = []
    for d in mdb.deputes.find({},{'depute_contacts':1,'depute_shortid':1,'_id':None}):
        newc = contacts.get(d['depute_shortid'],None)
        if not newc:
            continue
        dct = dict((c['type'],c['lien']) for c in d['depute_contacts'])
        dct.update(newc)
        d['depute_contacts'] = [ {'type':k,'lien':v} for k,v in dct.iteritems()]

        ops.append(UpdateOne({'depute_shortid':d['depute_shortid']},{'$set':{'depute_contacts':d['depute_contacts']}}))

    if ops:
        mdbrw.deputes.bulk_write(ops)
    return "ok"
def updateDeputesLieuNaissance():
    ops = []
    import re
    for d in mdb.deputes.find({},{'depute_shortid':1,'depute_naissance':1,'_id':None}):
        callback = lambda pat: pat.group(1)+' '+pat.group(2).upper()
        d['depute_naissance'] = re.sub(r'(\xe0|au|aux) (.*\xa0\()',callback,d['depute_naissance'])
        ops.append(UpdateOne({'depute_shortid':d['depute_shortid']},{'$set':{'depute_naissance':d['depute_naissance']}}))

    if ops:
        mdbrw.deputes.bulk_write(ops)
    return "ok"

def updateDeputesTravaux():
    ops = []

    stat_travaux = {}

    # TODO : stat GVT et commissions ?

    # Amendements rédigés
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs.id'}
    pipeline = [{'$match':{}},  {'$unwind':'$auteurs'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    for amdt in mdb.amendements.aggregate(pipeline):
        amd = amdt['_id']
        if not amd['depute'] in stat_travaux.keys():
            stat_travaux[amd['depute']] ={'amendements': {'auteur':0,'cosignataire':0 } }
        stat_travaux[amd['depute']]['amendements']['auteur'] += amdt['n']

    # Amendements cosignés
    pgroup['_id'] = {'depute':'$cosignataires.id'}
    pipeline = [{'$match':{}},  {'$unwind':'$cosignataires'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    for amdt in mdb.amendements.aggregate(pipeline):
        amd = amdt['_id']
        if not amd['depute'] in stat_travaux.keys():
            stat_travaux[amd['depute']] ={'amendements': {'auteur':0,'cosignataire':0 } }
        stat_travaux[amd['depute']]['amendements']['cosignataire'] += amdt['n']


    # Documents AN auteur
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs.id','type':'$typeid'}
    pipeline = [{'$match':{}},  {'$unwind':'$auteurs'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    for doc in mdb.documentsan.aggregate(pipeline):
        d = doc['_id']
        if not d['depute'] in stat_travaux.keys():
            stat_travaux[d['depute']] = {'documents':{}}
        if not 'documents' in stat_travaux[d['depute']].keys():
            stat_travaux[d['depute']]['documents'] = {}
        if not d['type'] in stat_travaux[d['depute']]['documents'].keys():
            stat_travaux[d['depute']]['documents'][d['type']] = {'auteur':0,'cosignataire':0}
        stat_travaux[d['depute']]['documents'][d['type']]['auteur'] += doc['n']

    pgroup['_id'] = {'depute':'$cosignataires.id','type':'$typeid'}
    pipeline = [{'$match':{}},  {'$unwind':'$cosignataires'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    for doc in mdb.documentsan.aggregate(pipeline):
        d = doc['_id']
        if not d['depute'] in stat_travaux.keys():
            stat_travaux[d['depute']] = {'documents':{}}
        if not 'documents' in stat_travaux[d['depute']].keys():
            stat_travaux[d['depute']]['documents'] = {}
        if not d['type'] in stat_travaux[d['depute']]['documents'].keys():
            stat_travaux[d['depute']]['documents'][d['type']] = {'auteur':0,'cosignataire':0}
        stat_travaux[d['depute']]['documents'][d['type']]['cosignataire'] += doc['n']



    # questions

    pgroup['_id'] = {'depute':'$depute', 'type':'$type'}
    pipeline = [{'$match':{}},  {"$group": pgroup }]
    for ques in mdb.questions.aggregate(pipeline):
        q = ques['_id']
        if not q['depute'] in stat_travaux.keys():
            stat_travaux[q['depute']] = {}
        if not 'questions' in stat_travaux[q['depute']].keys():
            stat_travaux[q['depute']]['questions'] = {}
        if not q['type'] in stat_travaux[q['depute']]['questions'].keys():
            stat_travaux[q['depute']]['questions'][q['type']] = 0
        stat_travaux[q['depute']]['questions'][q['type']] += ques['n']


    for d,stat in stat_travaux.iteritems():
        #print d,stat
        ops.append(UpdateOne({'depute_shortid':d},{'$set':{'depute_travaux':stat}}))
    if ops:
        mdbrw.deputes.bulk_write(ops)
