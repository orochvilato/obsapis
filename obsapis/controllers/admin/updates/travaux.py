# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne,ASCENDING
from string import Template

import datetime

def update_travaux(rebuild=False):
    # documents
    docs = {}
    categories = {''}
    mdbrw.travaux.ensure_index([("id", ASCENDING)])
    legislature = 15
    dnoms = dict((d['depute_shortid'],d['depute_nom']) for d in mdb.deputes.find({},{'depute_nom':1,'depute_shortid':1,'_id':None}))
    ops =[]
    s = 0
    deja = mdb.travaux.distinct('idori') if not rebuild else []
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
            auteurs = [_a['id'] for _a in doc['auteurs'] if _a['groupe']==g]
            auteurs_noms = [ dnoms[a] for a in auteurs ]
            tdoc.update(id=doc['id']+'_'+g,groupe=g,auteurs=auteurs, auteurs_noms = auteurs_noms)
            ops.append(UpdateOne({'id':doc['id']+'_'+g},{'$set':tdoc},upsert=True))

        auteurs  =[]
        for auteur in doc['auteurs']:
            if auteur.get('groupe',None):
                tdoc = dict(tdocbase)
                auteurs.append(auteur['id'])
                tdoc.update(id=doc['id']+'_'+auteur['id'],depute=auteur['id'],depute_nom=dnoms.get(auteur['id'],auteur['id']),auteur=True)
                ops.append(UpdateOne({'id':doc['id']+'_'+auteur['id']},{'$set':tdoc},upsert=True))


        for cosig in doc['cosignataires']:
            if cosig.get('groupe',None) and not cosig['id'] in auteurs:
                tdoc = dict(tdocbase)
                tdoc.update(id=doc['id']+'_'+cosig['id'],depute=cosig['id'],depute_nom=dnoms.get(cosig['id'],cosig['id']),auteur=False)
                ops.append(UpdateOne({'id':doc['id']+'_'+cosig['id']},{'$set':tdoc},upsert=True))
        #trav = dict(id=doc['id'],depute=doc[''])

    if ops:
        mdbrw.travaux.bulk_write(ops)

    print "done doc"
    desc = Template(u"Amendement n°${num} / ${art} / ${doc}")
    ops = []
    # ,{'id':{'$nin':deja}}]}
    for i,amd in enumerate(mdb.amendements.find({'legislature':legislature},
                                                {'date':1,'suppression':1,'dateDepot':1,'id':1,'urlAmend':1, 'sort':1,
                                                 'titreDossierLegislatif':1,'numAmend':1,'designationArticle':1,
                                                 'numInit':1,'auteurs':1,'cosignataires':1,'_id':1})):
        if amd['id'] in deja:
            continue
        if not 'date' in amd.keys():
            amd['date'] = datetime.datetime.strptime(amd['dateDepot'].replace('1er','1').encode('utf8'),'%d %B %Y')

        tamdbase = dict(date=amd['date'],idori=amd['id'],type='amendement',sort=amd['sort'],
                         type_libelle='Amendement',lien=amd['urlAmend'],suppression=amd.get('suppression',False),
                         dossier=amd['titreDossierLegislatif'],
                         description=desc.substitute(num=amd['numAmend'],art=amd['designationArticle'],doc=docs[amd['numInit']]))
        for g in list(set([_a['groupe'] for _a in amd['auteurs'] if 'groupe' in _a.keys()])):
            tamd = dict(tamdbase)
            auteurs=[_a['id'] for _a in amd['auteurs'] if _a['groupe']==g]
            auteurs_noms = [ dnoms[a] for a in auteurs]
            tamd.update(id=amd['id']+'_'+g,groupe=g,auteurs=auteurs, auteurs_noms=auteurs_noms)
            ops.append(UpdateOne({'id':amd['id']+'_'+g},{'$set':tamd},upsert=True))

        auteurs =  []
        for auteur in amd['auteurs']:
            if auteur.get('groupe',None):
                tamd = dict(tamdbase)
                auteurs.append(auteur['id'])
                tamd.update(id=amd['id']+'_'+auteur['id'],depute=auteur['id'],depute_nom=dnoms.get(auteur['id'],auteur['id']), auteur=True)
                ops.append(UpdateOne({'id':amd['id']+'_'+auteur['id']},{'$set':tamd},upsert=True))

        for cosig in amd['cosignataires']:
            if cosig.get('groupe',None) and not cosig['id'] in auteurs:
                tamd = dict(tamdbase)
                tamd.update(id=amd['id']+'_'+cosig['id'],depute=cosig['id'],depute_nom=dnoms.get(cosig['id'],cosig['id']), auteur=False)
                ops.append(UpdateOne({'id':amd['id']+'_'+cosig['id']},{'$set':tamd},upsert=True))



        if len(ops)>500:
            mdbrw.travaux.bulk_write(ops)
            ops = []
    if ops:
        mdbrw.travaux.bulk_write(ops)

    print "done amd"
    ops = []

    for q in mdb.questions.find({'legislature':legislature},{'date':1,'id':1,'type':1,'url':1,'ministere_interroge':1,'rubrique':1,'titre':1,'depute':1,'groupe':1}):
        if q['id'] in deja:
            pass
            continue

        qbase = dict(date=q['date'],idori=q['id'],type=q['type'],
                     type_libelle={'QE':'Question écrite','QG':'Question orale','QOSD':'Question orale sans débat'}[q['type']],
                     lien=q['url'],
                     dossier="%s / %s" % (q['ministere_interroge'],q['rubrique']),
                     description=q['titre'])
        qd = dict(qbase)
        qd.update(id=q['id']+'_'+q['depute'], depute = q['depute'], depute_nom = dnoms.get(q['depute'],q['depute']))
        ops.append(UpdateOne({'id':q['id']+'_'+q['depute']},{'$set':qd}, upsert=True))

        qg = dict(qbase)
        qg.update(id=q['id']+'_'+q['groupe'], groupe = q['groupe'], auteurs=[q['depute']], auteurs_noms=[dnoms.get(q['depute'],q['depute'])])
        ops.append(UpdateOne({'id':q['id']+'_'+q['groupe']},{'$set':qg}, upsert=True))
        if len(ops)>500:
            mdbrw.travaux.bulk_write(ops)
            ops = []
    if ops:
        mdbrw.travaux.bulk_write(ops)


    print "don ques"
