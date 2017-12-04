from obsapis import mdbrw,mdb
from pymongo import UpdateOne
import requests
import re
from fuzzywuzzy import fuzz
from obsapis.tools import strip_accents
def updateScrutinsTexte():
    docs = {}
    for doc in mdb.documentsan.find():
        dos = doc['dossier'].split('#')[0]
        if not dos in docs:
            docs[dos] = []
        docs[dos].append(doc['numero'])
    ops = []
    for s in mdb.scrutins.find({'scrutin_liendossier':{'$ne':None}},{'scrutin_typedetail':1,'scrutin_desc':1,'scrutin_id':1,'scrutin_num':1,'scrutin_liendossier':1}):
        if s['scrutin_typedetail']=='amendement':
            r = re.search(r'([0-9]+)',s['scrutin_desc'])
            if r:
                num = r.groups()[0]


                amdts = list(mdb.amendements.find({'$and':[{'instance':u"S\u00e9ance publique"},
                                                           {'urlDossierLegislatif':{'$regex':s['scrutin_liendossier']+'.*'}},
                                                           {'numInit':{'$in':docs[s['scrutin_liendossier']]}},
                                                           {'urlAmend':{'$regex':'/'+num+'.asp'}}]}))
                                                           #{'$or':[{'numAmend':num},{'numAmend':{'$regex':'.*[^0-9]'}{'$regex':'^'+num+'[^0-9].*'}},{'numAmend':{'$regex':'.*[^0-9]'+num+'$'}}]}]}))

                if len(amdts)!=1:
                    tr = 0
                    for a in amdts:
                        sig = strip_accents(a['signataires'].split(',')[0].split(' et ')[0].strip()).lower().split(' ')[-1]
                        s_desc = strip_accents(s['scrutin_desc']).lower().replace('premier','1er')
                        a_art = strip_accents(a['designationArticle']).lower().replace('premier','1er')


                        fz = 100 if a_art in s_desc else 0
                        fz += fuzz.partial_ratio(sig,s_desc) # +fuzz.partial_ratio(s_desc,sig)
                        #print (sig in s_desc),sig,s_desc
                        a['ratio'] = fz
                        a['sig'] = sig
                    amdts.sort(key=lambda a:a['ratio'],reverse=True)
                    if amdts[0]['ratio']<100:
                        print s['scrutin_num'],num,[(a['sig'],a['ratio']) for a in amdts]
                amdt = amdts[0]

                ops.append(UpdateOne({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_urlAmendement':amdt['urlAmend']}}))

    if ops:
        mdbrw.scrutins.bulk_write(ops)
