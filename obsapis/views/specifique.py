# -*- coding: utf-8 -*-

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
@app.route('/dupamd')
@cache_function(expires=0) #24*3600)
def dupamd():
    ct = {}
    for a in mdb.amendements.find({'sort':{'$ne':'Irrecevable'},'duplicate':{'$ne':None}},{'duplicate':1,'suppression':1}):
        if a['duplicate'] and not a.get('suppression'):
            ct[a['duplicate']] = ct.get(a['duplicate'],0)+1
    print sorted(ct.items(),key=lambda x:x[1])
    #import re
    #regx = re.compile("^<p[^>]*>Supprimer")
    #mdbrw.amendements.update_many({'$and':[{'suppression':None},{'dispositif':regx}]},{'$set':{'suppression':True}})
    #return json_response(mdb.amendements.find_one({'numInit':"485",'numAmend':"41"}))
    #a2 = mdb.amendements.find_one({'numInit':"237",'numAmend':"AS27"})['dispositif']
    items={}

    for a in mdb.amendements.find({'sort':{'$ne':'Irrecevable'},'duplicate':{'$eq':None}},{'_id':None,'numInit':1,'designationArticle':1,'urlTexteRef':1}).sort([("numInit",1),("designationArticle",1)]):
        txt = a['numInit']
        art = a['designationArticle']
        if not txt in items.keys():
            items[txt] = {}

        items[txt][art] = a['urlTexteRef']

    def remove_html_tags(text):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    from fuzzywuzzy import fuzz
    dups  = {}
    counts = {}
    ptxt = 0
    print len(items.keys())
    for txt in sorted(items.keys()):
        counts[txt] = 0
        for art in sorted(items[txt].keys()):
            mdbrw.dupamd.remove({'numInit':txt,'designationArticle':art})
            print txt,art
            counts[(txt,art)] = 0

            contents = []

            for amd in mdb.amendements.find({'sort':{'$ne':'Irrecevable'},'numInit':txt,'designationArticle':art},{'_id':None,'id':1,'dispositif':1,'auteurs':1,'urlAmend':1,'numAmend':1}):
                text = remove_html_tags(amd['dispositif'])
                
                contents.append(dict(doc=txt,auteur=amd['auteurs'][0],art=art,id=amd['id'],num=amd['numAmend'],url=amd['urlAmend'],content=text))

            if not txt in dups.keys():
                dups[txt] = {}
            if not art in dups[txt].keys():
                dups[txt][art] = []

            x = range(len(contents))

            while x:
                item=contents[x[0]]['content']
                matches = [x[0]]
                for cmp in x[1:]:
                    if fuzz.ratio(item,contents[cmp]['content'])>90:
                        matches.append(cmp)
                if len(matches)>1:
                    mtchs = []
                    for m in matches:
                        v = contents[m]
                        v['duplicate'] = True
                        mtchs.append(dict(id=v['id'],auteur=v['auteur'],num=v['num'],url=v['url']))
                    dups[txt][art].append(mtchs)
                    counts[(txt,art)] += len(matches)
                    counts[txt] += len(matches)
                x = [e for e in x if not e in matches]



            for dup in dups[txt][art]:
                id = mdbrw.dupamd.insert({'numInit':txt,'designationArticle':art})
                for d in dup:
                    mdbrw.amendements.update({'id':d['id']},{'$set':{'duplicate':id}})
            for c in contents:
                if not c.get('duplicate',False):
                    mdbrw.amendements.update({'id':c['id']},{'$set':{'duplicate':False}})


    html = "<html><body>"
    for txt in sorted(dups.keys(),key=lambda x:counts[x],reverse=True):
        html += u"<h3>%s (%d)</h3>" % (txt,counts[txt])
        for art in sorted(dups[txt].keys(),key=lambda x:counts[(txt,x)], reverse=True):
            html += u"<h4>%s (%d)</h4>" % (art,counts[(txt,art)])
            for dup in dups[txt][art]:
                html += '<p>'+', '.join('<span><a href={url}>{num} ({nom}/{gp})</a></span>'.format(url=d['url'],num=d['num'],nom=d['auteur']['id'],gp=d['auteur'].get('groupe','GVT')) for d in dup) + '</p>'

    html += '</body></html>'

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
