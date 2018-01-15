# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne
from string import Template

import datetime

def update_travaux():
    # documents
    docs = {}

    legislature = 15
    ops =[]
    s = 0
    deja = mdb.travaux.distinct('idori')
    #deja = []
    print len(deja)
    #print deja
    for doc in mdb.documentsan.find({'legislature':legislature},{'id':1,'numero':1,'date':1,'typeid':1,'type':1,'doclien':1,'dossier':1,'fulldesc':1,'auteurs':1,'cosignataires':1,'_id':1}):
        docs[doc['numero']] = doc['fulldesc']
        if doc['id'] in deja:
            continue
        if not 'date' in doc.keys():
            continue
        tdocbase = dict(date=doc['date'],idori=doc['id'],type=doc['typeid'],
                         type_libelle=doc['type'],lien=doc['doclien'],
                         dossier=doc['dossier'],description=doc['fulldesc'])
        for g in list(set([_a['groupe'] for _a in doc['auteurs'] if 'groupe' in _a.keys()])):
            tdoc = dict(tdocbase)
            tdoc.update(id=doc['id']+'_'+g,groupe=g,auteurs=[_a['id'] for _a in doc['auteurs'] if _a['groupe']==g])
            ops.append(UpdateOne({'id':doc['id']+'_'+g},{'$set':tdoc},upsert=True))

        for auteur in doc['auteurs']:
            if auteur.get('groupe',None):
                tdoc = dict(tdocbase)
                tdoc.update(id=doc['id']+'_'+auteur['id'],depute=auteur['id'],auteur=True)
                ops.append(UpdateOne({'id':doc['id']+'_'+auteur['id']},{'$set':tdoc},upsert=True))


        for cosig in doc['cosignataires']:
            if cosig.get('groupe',None):
                tdoc = dict(tdocbase)
                tdoc.update(id=doc['id']+'_'+cosig['id'],depute=cosig['id'],auteur=False)
                ops.append(UpdateOne({'id':doc['id']+'_'+cosig['id']},{'$set':tdoc},upsert=True))
        #trav = dict(id=doc['id'],depute=doc[''])

    if ops:
        mdbrw.travaux.bulk_write(ops)

    r="""
    id (D:numero),
    depute,
    date,
    auteur,
    groupe,
    type : D:typeid,A:amendement,Q:type
    typeLibelle
    lien: D:doclien, A:urlAmend, Q:url
    dossier: D:dossier, A:titreDossierLegislatif, Q: ministere_interroge/rubrique
    description: D:fulldesc, A:Amendement n°{numAmend}/{titreDossierLegislatif}/titre(numInit) doc"""

    desc = Template(u"Amendement n°${num} / ${art} / ${doc}")
    ops = []
    # ,{'id':{'$nin':deja}}]}
    for i,amd in enumerate(mdb.amendements.find({'legislature':legislature},
                                                {'date':1,'dateDepot':1,'id':1,'urlAmend':1, 'sort':1,
                                                 'titreDossierLegislatif':1,'numAmend':1,'designationArticle':1,
                                                 'numInit':1,'auteurs':1,'cosignataires':1,'_id':1})):
        if amd['id'] in deja:
            continue
        if not 'date' in amd.keys():
            amd['date'] = datetime.datetime.strptime(amd['dateDepot'].replace('1er','1').encode('utf8'),'%d %B %Y')

        print i
        tamdbase = dict(date=amd['date'],idori=amd['id'],type='amendement',sort=amd['sort'],
                         type_libelle='Amendement',lien=amd['urlAmend'],
                         dossier=amd['titreDossierLegislatif'],
                         description=desc.substitute(num=amd['numAmend'],art=amd['designationArticle'],doc=docs[amd['numInit']]))
        for g in list(set([_a['groupe'] for _a in amd['auteurs'] if 'groupe' in _a.keys()])):
            tamd = dict(tamdbase)
            tamd.update(id=amd['id']+'_'+g,groupe=g,auteurs=[_a['id'] for _a in amd['auteurs'] if _a['groupe']==g])
            ops.append(UpdateOne({'id':amd['id']+'_'+g},{'$set':tamd},upsert=True))

        for auteur in amd['auteurs']:
            if auteur.get('groupe',None):
                tamd = dict(tamdbase)
                tamd.update(id=amd['id']+'_'+auteur['id'],depute=auteur['id'],auteur=True)
                ops.append(UpdateOne({'id':amd['id']+'_'+auteur['id']},{'$set':tamd},upsert=True))


        for cosig in amd['cosignataires']:
            if cosig.get('groupe',None):
                tamd = dict(tamdbase)
                tamd.update(id=amd['id']+'_'+cosig['id'],depute=cosig['id'],auteur=False)
                ops.append(UpdateOne({'id':amd['id']+'_'+cosig['id']},{'$set':tamd},upsert=True))
        if len(ops)>500:
            print "write"
            mdbrw.travaux.bulk_write(ops)
            print i
            ops = []
    if ops:
        mdbrw.travaux.bulk_write(ops)
    print "fin"
