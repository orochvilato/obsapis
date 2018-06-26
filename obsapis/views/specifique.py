# -*- coding: utf-8 -*-
from flask import request
from obsapis import app,mdb,mdbrw

from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx,cache_function,json_response, strip_accents

@app.route('/gotravaux')
def gotravaux():
    from obsapis.controllers.admin.updates.travaux import update_travaux
    update_travaux()
    return 'ok'

@app.route('/supamd')
def supamd():
    gp = {}

    for amd in mdb.amendements.find({},{'suppression':1,'_id':None,'groupe':1,'auteurs':1}):

        g = amd['auteurs'][0].get('groupe',None)
        if not g:
            g = amd['auteurs'][0]['id']
        if not g in gp.keys():
            gp[g] = {'n':0,'s':0}
        if amd.get('suppression',None):
            gp[g]['s'] += 1
        gp[g]['n'] += 1
    gp = sorted(gp.items(),key=lambda x:float(x[1]['s'])/x[1]['n'], reverse=True)
    html = "<html><body><table border=1 cellpadding=10><thead><tr><th>Groupe</th><th>Nb amendements</th><th>Suppressions</th><th>%</th></tr></thead><tbody>"
    for k,v in gp:
        html += '<tr><td><strong>%s</strong></td><td>%d</td><td>%d</td><td>%.1f</td></tr>' % (k,v['n'],v['s'],100*float(v['s'])/v['n'])
    html += "</tbody></table></body></html>"
    return html

@app.route('/topdup')
def topdup():
    tops = {}
    for a in mdb.amendements.find({'$and':[{'suppression':{'$ne':True}},{'duplicate':{'$ne':False}},{'duplicate':{'$ne':None}}]},{'auteurs':1}):
        aut = a['auteurs'][0]['id']
        tops[aut] = tops.get(aut,0) + 1

    doc = '\n'.join("%s;%d" % (a,n) for a,n in sorted(tops.items(),key=lambda x:x[1], reverse=True))
    return doc


@app.route('/dupamd')
def dupamd():
    docs = {}
    dups = {}

    if not request.args:
        for doc in mdb.documentsan.find({},{'fulldesc':1,'numero':1,'doclien':1}):
            docs[doc['numero']] = doc
        for i,dup in enumerate(mdb.dupamd.find()):
            if dup.get('suppression','vide')=='vide':
                amd = mdb.amendements.find_one({'duplicate':dup['_id']},{'id':1,'_id':None,'urlTexteRef':1,'suppression':1})
                mdbrw.dupamd.update({'_id':dup['_id']},{'$set':{'id':amd['id'],'texturl':amd['urlTexteRef'],'suppression':amd.get('suppression',False)}})
                print i

            dup['textdesc'] = docs[dup['numInit']]['fulldesc']

            dups[dup['_id']] = dup
        pgroup = {}
        pgroup['n'] = {'$sum':1}
        pgroup['_id'] = { 'duplicate':'$duplicate'}
        pipeline = [{'$match':{'$and':[{'duplicate':{'$ne':False}},{'duplicate':{'$ne':None}}]}},
                    {'$group':pgroup},
                    {'$sort':{'n':-1}}]
        html = "<html><body><table border='1'><tbody>"
        for d in mdb.amendements.aggregate(pipeline):
            n = d['n']
            id = d['_id']['duplicate']
            #mdb.amendements.find_one({'duplicate':id},{'numInit':1,'designationArticle':1,})
            dup = dups[id]
            if dup['suppression']==False:
                html += '<tr><td width="50%"><a href="{texturl}"> {textdesc} / {art}</a></td><td width="10%"><a href="/dupamd?id={id}">{n}</a></td><td width="5%">{sup}</td></tr>'.format(n=n,id=id,art=dup['designationArticle'].encode('utf8'),texturl=dup['texturl'],textdesc=dup['textdesc'].encode('utf8'),sup=("*" if dup.get('suppression',False) else ''))
        html += '</tbody></table></body></html>'
        #dups_ids = [d['_id']['duplicate'] for d in dups if d['n']>1]

        #print dups_ids
        #print mdb.amendements.count({'duplicate':{'$in':dups_ids}})


    else:
        from bson.objectid import ObjectId
        id = request.args.get('id')
        html = "<html><body><table border='1'><tbody>"
        for amd in mdb.amendements.find({'duplicate':ObjectId(id)},{'auteurs':1,'numAmend':1,'urlAmend':1,'sort':1}).sort([('auteurs.groupe',1),('auteurs.id',1)]):
            grp = amd['auteurs'][0].get('groupe')
            aut = amd['auteurs'][0].get('id')
            sort = amd['sort'].encode('utf8')
            html += '<tr><td width="20%">{groupe}</td><td width="20%">{id}</td><td width="20%"><a href="{url}">{n}</a></td><td>{sort}</td></tr>'.format(n=amd['numAmend'],id=aut,sort=sort,groupe=grp,url=amd['urlAmend'])
        html += '</tbody></table></body></html>'
    return html



@app.route('/specifique/collaborateurs')
def collaborateurs():
    fds = ['Circo','Nom','Collaborateur']
    collabs = []
    for d in mdb.deputes.find({},{'depute_circo_id':1,'depute_nom':1,'depute_collaborateurs':1,'_id':None}):
        if d['depute_collaborateurs']:
            for c in d.get('depute_collaborateurs',[])+d.get('depute_collaborateurs_hatvp',[]):
                collabs.append({'Circo':d['depute_circo_id'],'Nom':d['depute_nom'],'Collaborateur':c})
    v = dictToXls(data={'sheets':['collaborateurs'],
                            'data':{'collaborateurs':{'fields':fds,'data':collabs},
                                   }})
    return xls_response('collaborateursAN',v)

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

    return xls_response('documentsAN',v)
