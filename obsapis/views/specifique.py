
from obsapis import app,mdb,mdbrw

from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx

@app.route('/gotravaux')
def gotravaux():
    from obsapis.controllers.admin.updates.travaux import update_travaux
    update_travaux()
    return 'ok'


@app.route('/specifique/proplois')
def proplois():
    flds = [u"Proposition de loi",u"Projet de loi",u"Proposition de r\xe9solution",u"Rapport",u"Rapport d'information",u"Avis",u"Allocution"]
    #flds = ['Proposition de r\xe9solution', 'Proposition de loi', 'Rapport', 'Allocution', 'Avis', "Rapport d'information", 'Projet de loi']

    fieldlist = [('numero','Num'),
                                             ('description','Description'),
                                             ('sig1','Auteur'),
                                             ('sig1gp','Groupe'),
                                             ('sigs','Autres signataires'),
                                             ('dossier','Dossier'),
                                             ('doclien','Lien document'),
                                             ('dossierlien','Lien dossier')]
    docs = {}
    depnoms = dict((d['depute_shortid'],d['depute_nomcomplet']) for d in mdb.deputes.find({},{'depute_shortid':1,'depute_nomcomplet':1,'groupe_abrev':1}))
    for doc in mdb.documentsan.find({},{'type':1,'titre':1,'auteurs':1,'cosignataires':1,'fulldesc':1,'dossier':1,'dossierlien':1,'doclien':1,'numero':1,'_id':None}):
        if doc['numero'][0:2]=='TA':
            continue
        aut = doc['auteurs'][0]['id']
        doc['sig1'] = depnoms.get(aut,aut)
        doc['sig1gp'] = doc['auteurs'][0].get('groupe','')
        doc['sigs'] = ', '.join([ "%s (%s)" % (depnoms[d['id']],d['groupe']) for d in doc['auteurs'][1:]+doc['cosignataires']])
        doc['description'] = doc['fulldesc'] #.encode('iso8859-1').replace('\n','')
        doc['dossier'] = doc['dossier'] #.encode('iso8859-1')


        if not doc['type'] in docs.keys():
            docs[doc['type']] = []
        docs[doc['type']].append(doc)
    data = {}
    data['sheets'] = flds
    #print docs.keys()
    data['data'] = dict((k,dict(fields=fieldlist,data=v)) for k,v in docs.iteritems())
    v = dictToXls(data=data)
    return xls_response('documentsAN.xls',v)
    v = dictToXls(data={'sheets':['propositions de loi','projets de loi','autres'],
                        'data':{'propositions de loi':{'fields':[('numero','Num'),
                                                                 ('description','Description'),
                                                                 ('sig1','Auteur'),
                                                                 ('sig1gp','Groupe'),
                                                                 ('sigs','Autres signataires'),
                                                                 ('dossier','Dossier'),
                                                                 ('doclien','Lien document'),
                                                                 ('dossierlien','Lien dossier')],'data':proploi},
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
