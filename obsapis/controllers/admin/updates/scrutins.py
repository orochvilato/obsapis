# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne,UpdateMany
import requests
import re
from fuzzywuzzy import fuzz
from obsapis.tools import strip_accents
def updateScrutinsTexte():
    depgp = dict((d['depute_shortid'],d['groupe_abrev']) for d in mdb.deputes.find({},{'depute_shortid':1,'groupe_abrev':1,'_id':0}))
    docs = {}
    docsgp = {}
    for doc in mdb.documentsan.find({},{'dossierlien':1,'numero':1}):
        dos = doc['dossierlien'].split('#')[0]
        if not dos in docs:
            docs[dos] = []
        docs[dos].append(doc['numero'])
        sig = doc.get('signataires',None)
        if sig:
            sig = depgp[sig[0]]
        else:
            sig = "Gouvernement"
        docsgp[doc['numero']] = sig


    ops = []
    vote_ops = []
    filter = {'scrutin_liendossier':{'$ne':None}}
    #filter = {'$text':{'$search':'"sous-amendement"'}}
    for s in mdb.scrutins.find(filter,{'scrutin_typedetail':1,'scrutin_lientexte':1,'scrutin_desc':1,'scrutin_id':1,'scrutin_num':1,'scrutin_liendossier':1}):
        #print s['scrutin_num']
        if s['scrutin_typedetail']!='amendement':
            #print s['scrutin_lientexte'],s['scrutin_num']
            if 'scrutin_lientexte' in s.keys():
                gp = docsgp.get(s['scrutin_lientexte'][0][2],'Gouvernement')
            else:
                gp = "Gouvernement"

            ops.append(UpdateOne({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_groupe':gp}}))
            vote_ops.append(UpdateMany({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_groupe':gp}}))
        else: #Amendement
            #r = re.search(r'([0-9]+)',s['scrutin_desc'])
            r = re.findall(r'amendement[^0-9]+([0-9]+)',s['scrutin_desc'])
            found = []
            for num in r:
            #if r:

                #num = r.groups()[0]
                #print s
                #print s['scrutin_liendossier']
                #print docs[s['scrutin_liendossier']]
                amdts = list(mdb.amendements.find({'$and':[{'instance':u"S\u00e9ance publique"},
                                                           {'urlDossierLegislatif':{'$regex':s['scrutin_liendossier']+'.*'}},
                                                           {'numInit':{'$in':docs[s['scrutin_liendossier']]}},
                                                           {'urlAmend':{'$regex':'/'+num+'.asp'}}]}))
                                                           #{'$or':[{'numAmend':num},{'numAmend':{'$regex':'.*[^0-9]'}{'$regex':'^'+num+'[^0-9].*'}},{'numAmend':{'$regex':'.*[^0-9]'+num+'$'}}]}]}))


                if len(amdts)!=1:
                    tr = 0
                    for a in amdts:
                        sig = a['auteurs'][0]['id']
                        #sig = strip_accents(a['signataires'].split(',')[0].split(' et ')[0].strip()).lower().split(' ')[-1]
                        s_desc = strip_accents(s['scrutin_desc']).lower().replace('premier','1er')
                        a_art = strip_accents(a['designationArticle']).lower().replace('premier','1er')


                        fz = 100 if a_art in s_desc else 0
                        fz += fuzz.partial_ratio(sig,s_desc) # +fuzz.partial_ratio(s_desc,sig)
                        #print (sig in s_desc),sig,s_desc
                        a['ratio'] = fz
                        a['sig'] = sig
                    amdts.sort(key=lambda a:a['ratio'],reverse=True)
                    #if amdts[0]['ratio']<100:
                        #print s['scrutin_num'],num,[(a['sig'],a['ratio']) for a in amdts]
                amdt = amdts[0]
                found.append(amdt)
            if found:
                liens =  s['scrutin_lientexte']
                amdt = found[0]
                siggp = amdt['auteurs'][0]['groupe'] if 'groupe' in amdt['auteurs'][0].keys() else 'Gouvernement'
                #if len(amdt.get('signataires_groupes',[]))>0:
                #    siggp = amdt['signataires_groupes'][0]
                #else:
                #    siggp = 'Gouvernement'
                updS = {'scrutin_groupe':siggp,'scrutin_urlAmendement':amdt['urlAmend']}
                if amdt['urlTexteRef']:
                    liens[0][1] = amdt['urlTexteRef']
                if len(found)>1: # amendement de ref au sous-amendement
                    liens.append([found[1]['numAmend'],found[1]['urlAmend'],None])
                ops.append(UpdateOne({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_lientexte':liens}}))
                #mdbrw.scrutins.update_one({'scrutin_num':s['scrutin_num']},{'$set':updS})
                vote_ops.append(UpdateMany({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_groupe':siggp}}))

    if ops:
        mdbrw.scrutins.bulk_write(ops)
        mdbrw.votes.bulk_write(vote_ops)
