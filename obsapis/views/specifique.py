# -*- coding: utf-8 -*-

from obsapis import app,mdb,mdbrw

from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx,cache_function,json_response

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
@app.route('/dupamd')
@cache_function(expires=0) #24*3600)
def dupamd():
    #import re
    #regx = re.compile("^<p[^>]*>Supprimer")
    #mdbrw.amendements.update_many({'$and':[{'suppression':None},{'dispositif':regx}]},{'$set':{'suppression':True}})
    #return json_response(mdb.amendements.find_one({'numInit':"485",'numAmend':"41"}))
    #a2 = mdb.amendements.find_one({'numInit':"237",'numAmend':"AS27"})['dispositif']
    import hashlib

    docs = [ num for num in mdb.amendements.distinct('numInit') if num[:2]!='TA' ]
    #docs = docs[:5]
    identiques = []
    suppr = []
    for doc in docs:
        amds = {}


        for amd in mdb.amendements.find({'numInit':doc,'dispositif':{'$ne':''},'suppression':{'$ne':True},'groupe':{'$ne':None}},{'suppression':1,'numAmend':1,'auteurs':1,'urlAmend':1,'dispositif':1,'sort':1,'designationArticle':1}):
            num = amd['numAmend']
            txt = amd['dispositif'].encode('utf8')
            art = amd['designationArticle']
            url = amd['urlAmend']
            if amd.get('suppression',None):
                suppr.append("%s-%s" % (doc,num))
            auteur = amd['auteurs'][0]
            if not art in amds:
                amds[art] = []
            amds[art].append((("%s-%s" % (doc,num),auteur['id'],auteur['groupe'],amd['sort'],url),hashlib.md5(txt).hexdigest()))

        for art,artamds in amds.iteritems():

            dups = {}
            for id,hash in artamds:
                dups.setdefault(hash,[]).append(id)
            dups = [ v for k,v in dups.iteritems() if len(v)>1 ]
            if dups:
                identiques += dups

    #return json_response(identiques)

    decpt_auteur = {}
    decpt_groupe = {}
    liste_groupe = {}
    decpt_amd = {}
    for same in identiques:
        amdt = (same[0][0],same[0][4])
        autres = []
        grps = []
        auts = []
        for amd,auteur,groupe,sort,url in same:
            decpt_auteur[auteur] = decpt_auteur.get(auteur,0) +1
            decpt_groupe[groupe] = decpt_groupe.get(groupe,0) +1

            if not groupe in grps:
                liste_groupe.setdefault(groupe,[]).append(same)
                grps.append(groupe)
            autres.append((amd,url))
        decpt_amd[amdt] = autres


    html = u"<h3>Députés</h3><ul><li>"+"</li><li>".join([ '%s (%d)' % r for r in sorted(decpt_auteur.items(),key=lambda x:x[1], reverse=True)][:30])+"</ul>"
    html += u"<h3>Groupes</h3><ul><li>"+"</li><li>".join([ '%s (%d)' % r for r in sorted(decpt_groupe.items(),key=lambda x:x[1], reverse=True)][:30])+"</ul>"

    for g in ['FI']:
        html += u"<h3>Duplicats groupe %s</h3><ul><li>" % g
        items = []
        for idts in liste_groupe[g]:
            item = ', '.join(['<a href="%s">%s (%s)</a>' % (id[4],id[0],id[2]) for id in idts])
            items.append(item)
        html += "</li><li>".join(items)+"</ul>"

    items = []

    for amd,autres in sorted(decpt_amd.items(),key=lambda x:len(x[1]), reverse=True):
        item = '<a href="%s">%s</a>' % (amd[1],amd[0])+' (%d) : ' % (len(autres))
        item += ', '.join(['<a href="%s">%s</a>' % (at[1],at[0]) for at in autres])
        items.append(item)
    html += u"<h3>Amendements</h3><ul><li>"+"</li><li>".join(items)+"</ul>"
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
