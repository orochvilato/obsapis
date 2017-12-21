from obsapis import app,mdb,mdbrw

from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx

@app.route('/specifique/proplois')
def proplois():
    proploi = []
    projloi = []
    autres = []
    depnoms = dict((d['depute_shortid'],{'nom':d['depute_nomcomplet'],'groupe':d['groupe_abrev']}) for d in mdb.deputes.find({},{'depute_shortid':1,'depute_nomcomplet':1,'groupe_abrev':1}))
    for doc in mdb.documentsan.find():
        if doc['numero'][0:2]=='TA':
            continue
        if 'signataires' in doc.keys() and len(doc['signataires'])>0:
            doc['sig1'] = depnoms[doc['signataires'][0]]['nom']
            doc['sig1gp'] = depnoms[doc['signataires'][0]]['groupe']
            doc['sigs'] = ', '.join([ "%s (%s)" % (depnoms[d]['nom'],depnoms[d]['groupe']) for d in doc['signataires'][1:]])
        doc['description'] = doc['description'].encode('iso8859-1').replace('\n','')
        doc['titre'] = doc['titre'].encode('iso8859-1')


        if doc['description'][0:13]=='Projet de loi':
            projloi.append(doc)
        elif doc['description'][0:18]=='Proposition de loi':
            proploi.append(doc)
        else:
            autres.append(doc)
    v = dictToXls(data={'sheets':['propositions de loi','projets de loi','autres'],
                        'data':{'propositions de loi':{'fields':[('numero','Num'),
                                                                 ('description','Description'),
                                                                 ('sig1','Auteur'),
                                                                 ('sig1gp','Groupe'),
                                                                 ('sigs','Autres signataires'),
                                                                 ('titre','Dossier'),
                                                                 ('document','Lien document'),
                                                                 ('dossier','Lien dossier')],'data':proploi},
                                'projets de loi':{'fields':[('numero','Num'),
                                                             ('description','Description'),
                                                             ('titre','Dossier'),
                                                             ('document','Lien document'),
                                                             ('dossier','Lien dossier')],'data':projloi},
                                'autres':{'fields':[('numero','Num'),
                                                             ('description','Description'),
                                                             ('titre','Dossier'),
                                                             ('document','Lien document'),
                                                             ('dossier','Lien dossier')],'data':autres}}})

    return xls_response('documentsAN.xls',v)
