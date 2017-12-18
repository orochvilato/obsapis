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