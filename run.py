# -*- coding: utf-8 -*-

from obsapis import app,mdb,mdbrw,use_cache
from obsapis.tools import normalize
from flask import render_template
from bson import json_util

import xmltodict
import requests
import re
from pymongo import UpdateOne
from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx,image_response
from obsapis.controllers.admin.imports.documents import import_docs
from obsapis.controllers.admin.imports.amendements import import_amendements
from obsapis.controllers.admin.updates.amendements import update_amendements
from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte
from obsapis.controllers.admin.updates.deputes import updateDeputesTravaux
from obsapis.controllers.admin.updates.travaux import update_travaux
from obsapis.controllers.admin.imports.liensdossierstextes import import_liendossierstextes
from obsapis.controllers.visuel.generateur import gentest
from obsapis.controllers.admin.imports.qag import import_qag


@app.route('/amdc')
def amdcs():
    gps = {}
    dps = {}
    for a in mdb.amendements.find({},{'suppression':1,'auteur':1,'groupe':1,'_id':None}):
        d = a['auteur']
        g = a['groupe']
        if not d in dps.keys():
            dps[d] = {'sup':0,'n':0}
        if not g in gps.keys():
            gps[g] = {'sup':0,'n':0}
        if a.get('suppression',False):
            gps[g]['sup'] += 1
            dps[d]['sup'] += 1
        gps[g]['n'] += 1
        dps[d]['n'] += 1

    for k,v in gps.iteritems():
        print k,v['sup'],v['n'],round(100*float(v['sup'])/v['n'],2)
    for k,v in sorted(dps.iteritems(),key=lambda x:float(x[1]['sup'])/x[1]['n'] if x[1]['n'] else 0,reverse=True)[:20]:
        print k,v['sup'],v['n']

    return "ok"

@app.route('/amd')
def amds():
    import_amendements()
    update_amendements()
    #return "ok"
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs.id'}
    pgroup['_id']['sort'] ='$sort'
    pipeline = [{'$match':{}}, {'$unwind':'$auteurs'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    stat_amdts = {}
    for amdt in mdb.amendements.aggregate(pipeline):
        if amdt['_id']['depute']=='lisemagnier':
            print amdt['_id']['sort'],amdt['n']
        amd = amdt['_id']
        if not amd['depute'] in stat_amdts.keys():
            stat_amdts[amd['depute']] = {'rediges':0,'adoptes':0,'cosignes':0}
        if amd['sort']==u'Adopté':
            stat_amdts[amd['depute']]['adoptes'] += amdt['n']

        stat_amdts[amd['depute']]['rediges'] += amdt['n']

    return json_response(stat_amdts)

@app.route('/refs')
def refs():
    import re
    ops = import_liendossierstextes()
    return json_util.dumps(ops)
@app.route('/csa')
def csa():
    import requests
    import lxml.html
    from StringIO import StringIO
    itvs = []
    r = requests.get('http://www.csa.fr/csapluralisme/tableau?annee=2017')
    html = lxml.html.fromstring(r.content)
    for url in html.xpath('//tr[td[text()[contains(.,"PERSONNALITES POLITIQ7UES")]]]/td[3]/a/@href'):
        print url
        fullurl = 'http://www.csa.fr'+url
        r = requests.get(fullurl)
        parse = csa_pdf(StringIO(r.content))
        if parse=='boom':
            1/0
        itvs += parse

    f = open('test.csv','w')
    for itv in itvs:
        f.write(";".join([itv['chaine'],"%d-%d" % itv['date'],itv['type'],itv['nom'],itv['org'],itv['duree']])+'\n')
    return "ok"

    return json_response(itvs)

def csa_pdf(document):
    chaines = {  2752:'FRANCE INTER',
                    2746:'FRANCE INTER',
                    3054:'FRANCE INTER',
                    2845:'FRANCE INFO',
                    2314:'FRANCE CULTURE',
                    3116:'RADIO CLASSIQUE',
                    2152:'BFM',
                    3249:'RMC',
                    2481:'EUROPE 1',
                    2897:'RTL',
                    1575:'TF1',
                    6084:'FRANCE 2',
                    5694:'FRANCE 3',
                    1563:'FRANCE 3',
                    8237:'CANAL+',
                    18914:'FRANCE 5',
                    7541:'M6',
                    1857:'C8',
                    1818:'C8',
                    1931:'TMC',
                    2301:'BFMTV',
                    1872:'CNEWS',
                    1833:'LCI',
                    2329:'FRANCEINFO',
                    5937:'FRANCEINFO',
                    2460:'FRANCEINFO'}
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfinterp import PDFPageInterpreter
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.pdfpage import PDFPage
    from pdfminer.layout import LTTextBoxHorizontal,LTFigure,LTImage
    itvs = []

    #Create resource manager
    rsrcmgr = PDFResourceManager()
    # Set parameters for analysis.
    laparams = LAParams()
    # Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    chaine = ""
    info = False
    for page in PDFPage.get_pages(document):
        #print "page-----------"
        interpreter.process_page(page)
        # receive the LTPage object for the page.
        layout = device.get_result()
        elts = dict(noms=[],orgs=[],durees=[])
        go = False
        col =""
        for element in layout:
            #print element
            if isinstance(element, LTFigure):
                for e in element:
                    if isinstance(e, LTImage):
                        if e.stream:
                            data = e.stream.get_rawdata()
                            chaine = chaines[len(data)]
                            #print len(data)
            if isinstance(element, LTTextBoxHorizontal):
                x = element.x1
                txt = element.get_text().strip()
                if 'TELEVISION' in txt or 'INTERVENTION' in txt or 'PROGRAMMES' in txt:
                    go = False
                if 'TELEVISIONS (AUTRES' in txt:
                    info = False
                if 'TELEVISIONS -' in txt:
                    info = True
                #print txt
                if txt[0:3]=='Du ':
                    date = (int(txt[9:13]),int(txt[6:8]))
                if txt in ['MAG','JT','PROG']:
                    typ = txt
                if go:
                    if x<seuils[0]:
                        col = 'noms'
                    elif x<seuils[1]:
                        col = 'orgs'
                    else:
                        col = 'durees'
                        txt = int(txt[0:2])*3600+int(txt[3:5])*60+int(txt[6:8])
                        #print "-->",txt
                    #print x,txt,col
                    elts[col].append((txt,date,typ))
                if txt==u'Dur\xe9e':
                    seuils = [250 if info else 220,500]
                    go = True
                elif txt==u'DUREE':
                    seuils = [260,480]
                    go = True

        if (len(elts['noms'])==len(elts['orgs']) or len(elts['noms'])==len(elts['durees'])):
            for i in range(len(elts['noms'])):
                itvs.append(dict(chaine=chaine,nom=elts['noms'][i][0],org=elts['orgs'][i][0],duree=elts['durees'][i][0],
                                 date=elts['durees'][i][1],
                                 type=elts['durees'][i][2]
                                 )
                            )
        else:
            return "boom"
            print len(elts['noms']),len(elts['orgs']),len(elts['durees'])
    return itvs

@app.route('/updateScrutins')
def updScrutins():
    updateScrutinsTexte()
    return "ok"
@app.route('/ouv')
def ouv():
    depgp = dict((d['depute_shortid'],{'img':'http://www2.assemblee-nationale.fr/static/tribun/15/photos/'+d['depute_uid'][2:]+'.jpg','g':d['groupe_abrev'],'n':d['depute_nom']}) for d in mdb.deputes.find({},{'depute_nom':1,'depute_uid':1,'depute_shortid':1,'groupe_abrev':1,'_id':None}))
    shortids = dict((d['depute_id'],d['depute_shortid']) for d in mdb.deputes.find({},{'depute_id':1,'depute_shortid':1,'_id':None}))
    depsig = {}
    for doc in mdb.documentsan.find({'signataires':{'$ne':None}},{'numero':1,'signataires':1,'_id':None}):
        if doc['signataires']:
            sig1 = doc['signataires'][0]
            if sig1:
                for sig in doc['signataires'][1:]:
                    if sig and depgp[sig1]['g']!=depgp[sig]['g'] and depgp[sig]['g']!='NI':
                        if sig=='mohamedlaqhila':
                            print doc

                        depsig[sig] = depsig.get(sig,0)+1

    for amd in mdb.amendements.find({},{'numAmend':1,'signataires_ids':1,'_id':None}):
        if not amd['signataires_ids']:
            continue
        sig1 = shortids.get(amd['signataires_ids'][0],None)
        if sig1:
            for sig in amd['signataires_ids'][1:]:
                sig2 = shortids[sig]
                if sig2 and depgp[sig1]['g']!=depgp[sig2]['g'] and depgp[sig2]!='NI':
                    if sig2=='mohamedlaqhila':
                        print amd
                    depsig[sig2] = depsig.get(sig2,0)+1

    return json_response(sorted(depsig.iteritems(),key=lambda x:x[1],reverse=True))


@app.route('/testcompat')
def testcompat():

    #return json_response(list(mdb.scrutins.find({'$and':[{'scrutin_amendement_groupe':None},{'scrutin_typedetail':'amendement'}]},{'scrutin_num':1})))
    #for gid in ['FI','GDR','UAI','LR','MODEM','NG','REM']:
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$depute_shortid'}
    pgroup['_id']['position'] ='$vote_position'
    pgroup['_id']['groupe'] = '$scrutin_groupe'
    pipeline = [{'$match':{}},   {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    voteamdts = {}
    for voteamdt in mdb.votes.aggregate(pipeline):
            depuid = voteamdt['_id']['depute']
            pos = voteamdt['_id']['position']
            gp = voteamdt['_id']['groupe']
            if not depuid in voteamdts.keys():
                voteamdts[depuid] = {}
            if not gp in voteamdts[depuid].keys():
                voteamdts[depuid][gp] = {}
            voteamdts[depuid][gp][pos] = voteamdts[depuid][gp].get(pos,0) + voteamdt['n']
    return json_response(voteamdts['mariechristineverdierjouclas'])


@app.route('/testgen')
def viewtestgen():
    return image_response('png',gentest())
@app.route('/hatvp')
def hatvp():
    from obsapis.controllers.admin.imports.hatvp import update_hatvp
    update_hatvp()
    return json_response(mdb.deputes.find_one({},{'depute_collaborateurs_hatvp':1}))


@app.route('/hatvpinter')
def hatvpinter():
     if 0:
         r = requests.get('http://www.hatvp.fr/agora/opendata/agora_repertoire_opendata.json')
         content = r.content
         open('/tmp/decs','w').write(content)
     else:
         content = open('/tmp/decs','r').read()
     import json
     decs = json.loads(content)
     nodes = []
     links = []

     for i,fiche in enumerate(decs['publications']):
         print i
         id = fiche['identifiantNational']
         r =requests.get('http://www.hatvp.fr/fiche-organisation/?organisation='+fiche['identifiantNational']+'#')
         if rien not in r.content:
             print "-->",id
             ids.append(id)
     return json_response(ids)
@app.route('/test')
def test():

    #import_qag()
    return json_response(mdb.questions.count())
    #return json_response(mdb.interventions.find({'itv_rapporteur':None})))
    #return json_response(mdb.interventions.find({'itv_rapporteur':None}).distinct('itv_date'))
    #return json_response(mdb.interventions.find({'$and':[{'itv_rapporteur':True},{'depute_shortid':'ericcoquerel'}]}))
    from obsapis.controllers.admin.updates.interventions import update_stats_interventions
    deppdp  = {}
    #return json_response(update_stats_interventions())
    for pdp in update_stats_interventions():

        dep = pdp['_id'].get('depute',None)
        if dep:
            if not dep in deppdp.keys():
                deppdp[dep]= dict(n=0,rap=0)
            deppdp[dep]['rap' if pdp['_id']['rapporteur'] else 'n'] += pdp['n']

    return json_response(', '.join('%d. %s (%d)' % (i+1,d[0],d[1]['n']+d[1]['rap']) for i,d in enumerate(sorted(deppdp.items(),key=lambda x:x[1]['n']+x[1]['rap'],reverse=True))))
    counts = {}
    nbmembres = dict((g['groupe_abrev'],g['groupe_nbmembres']) for g in mdb.groupes.find({},{'groupe_abrev':1,'groupe_nbmembres':1}))
    for q in mdb.questions.find({'groupe':{'$ne':None}},{'groupe':1}):
        g = q['groupe']
        if not g in counts.keys():
            counts[g] = 0
        counts[g] += 1
    return json_response([ "%s (%d)" % (g,n/nbmembres[g]) for g,n in sorted(counts.items(),key=lambda x:x[1]/nbmembres[x[0]],reverse=True)])
    col = []
    for d in mdb.deputes.find({},{'depute_collaborateurs_hatvp':1,'_id':None,'depute_shortid':1}):
        col.append((d['depute_shortid'],len(d.get('depute_collaborateurs_hatvp',[]))))
    return json_response(sorted(col,key=lambda x:x[1],reverse=True)[:20])

    import datetime
    #mdbrw.deputes.update_one({'depute_shortid':'michelevictory'},{'$unset':{'stats.commissions':""}})
    return json_response(mdb.deputes.find_one({},{'depute_hatvp':1}))
    return json_response([d['depute_shortid'] for d in mdb.deputes.find({'stats.commissions.present':0.0})])
    #{'$and': [{'depute_actif': True}, ]} [('stats.nonclasse', 1), ('stats.ranks.down.exprimes', 1)]
    return json_response(list(d['depute_shortid'] for d in mdb.deputes.find({'depute_mandat_debut':{'$gte':datetime.datetime(2017,5,21)}},{'depute_shortid':1})))

    return json_response([d['depute_shortid'] for d in mdb.deputes.find({'$and':[{'$or':[{'depute_actif': True},{'depute_shortid':'michelevictory'}]},{u'stats.positions.exprimes': {'$ne': None}}]}).sort([('stats.nonclasse', 1), ('stats.ranks.down.exprimes', 1)]).limit(5)])
    for d in mdb.deputes.find({'depute_election':None}):
        circo = d['depute_circo_id']
        titulaire = mdb.deputes.find_one({'$and':[{'depute_circo_id':circo},{'depute_election':{'$ne':None}}]})
        mdbrw.deputes.update_one({'depute_shortid':d['depute_shortid']},{'$set':{'depute_election':titulaire['depute_election']}})
    return "oj"
    #mdbrw.questions.update_many({'legislature':None},{'$set':{'legislature':15}})
    #update_travaux()
    #return json_response(mdb.interventions.find_one({}))
    return json_response(list(q['itv_contenu_texte'] for q in mdb.interventions.find({'depute_shortid':'mariechristineverdierjouclas'})))

    return json_response(mdb.travaux.distinct('type'))

    #for a in mdb.amendements.find({'suppression':True},{'id':1}):
    #    mdbrw.travaux.update_many({'idori':a['id']},{'$set':{'suppression':True}})

    #mdbrw.travaux.remove({'idori':'S-AMANR5L15PO419610B155N7'})
    #mdbrw.amendements.remove({'id':{'$in':amdlist}})
    #mdbrw.travaux.remove({'idori':{'$in':amdlist}})
    #import_amendements()


    return json_response(list(q['description'] for q in mdb.travaux.find({'$and':[{'auteur':{'$ne':False}},{'type':'QE'},{'depute':'francoisruffin'}]})))

    return json_response(list(mdb.travaux.find({'idori':'S-AMANR5L15PO419610B155N7'})))


    print mdb.travaux.count()
    return json_response(list(t['description'] for t in mdb.travaux.find({'groupe':'FI'})))

    #updateDeputesTravaux()

    #importdocs()


    #import_qag()

    return json_response(mdb.deputes.find_one({'depute_shortid':'francoisruffin'}))
    #importdocs()

    #return json_response(mdb.documentsan.find_one({'$and':[{'typeid':'propositionderesolution'},{'cosignataires.id':'francoisruffin'}]}))
    ops = []
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs'}

    pipeline = [{'$match':{}}, {'$unwind':'$auteurs'},{"$group": pgroup }] #'scrutin_typedetail':'amendement'
    return json_response(sum(d['n'] for d in mdb.documentsan.aggregate(pipeline)))
    print len(list(mdb.documentsan.aggregate(pipeline))),mdb.documentsan.count()


    #return json_response(mdb.amendements.find({'suppression':True},{'dispositif':1}).count())
    #mdbrw.scrutins.update_one({'scrutin_num':324},{'$set':{'scrutin_liendossier':'http://www.assemblee-nationale.fr/15/dossiers/deuxieme_collectif_budgetaire_2017.asp'}})
    #return json_util.dumps(list(mdb.amendements.find({'numAmend':'426'})))
    #mdbrw.scrutins.update_one({'scrutin_num':1},{'$set':{'scrutin_groupe':'Gouvernement','scrutin_lientexte':[(u'déclaration de politique générale',
    #                                                                          'http://www.gouvernement.fr/partage/9296-declaration-de-politique-generale-du-premier-ministre-edouard-philippe',
    #
    #mdbrw.votes.update_many({'scrutin_num':1},{'$set':{'scrutin_groupe':'Gouvernement'}})


    #return json_response([ (d['depute_shortid'],d['depute_mandat_fin_cause']) for d in mdb.deputes.find({'depute_actif':False},{'depute_shortid':1,'depute_mandat_fin_cause':1,'_id':None})])
    #mdbrw.scrutins.update_one({'scrutin_num':357},{'$set':{'scrutin_lientexte.0.1':'http://www.assemblee-nationale.fr/15/dossiers/jeux_olympiques_paralympiques_2024.asp#'}})
    #return json_response(mdb.scrutins.find_one({'scrutin_num':357}))
    return json_response(mdb.documentsan.distinct('type'))

    # visuels
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'depute':'$depute'}
    pipeline = [{'$match':{'name':'visuelstat'}},{'$group':pgroup}]
    vdeps = []
    for g in mdb.logs.aggregate(pipeline):
        _g = g['_id']['depute']
        if _g != None:
            vdeps.append((_g,g['n']))

    return ", ".join([ "%s (%s)" % i for i in sorted(vdeps,key=lambda x:x[1],reverse=True)])

    #updateDeputesContacts()
    return json_util.dumps(mdb.deputes.find_one({'depute_shortid':'nicolelepeih'},{'depute_contacts':1,'_id':None}))
    #importdocs()
    #return json_util.dumps(list(mdb.logs.find({'name':'visuelstat'})))
    mts = list(mdb.scrutins.find({ '$text': { '$search': "rejet" } },{'scrutin_groupe':1,'scrutin_fulldesc':1,'scrutin_sort':1,'_id':None}))
    _mts = "\n".join([";".join([m.get('scrutin_groupe',''),m['scrutin_sort'],m['scrutin_fulldesc']]) for m in mts])
    print _mts

    return json_util.dumps(mdb.deputes.find_one({'depute_shortid':'thierrysolere'},{'stats':1,'_id':None}))

    return json_util.dumps([(d['depute_nom'],
                             d['stats']['positions']['exprimes'],
                             d['stats']['votesamdements']['pctpour'],
                             d['depute_shortid']) for d in mdb.deputes.find({'groupe_abrev':'REM','stats.positions.exprimes':{'$gt':20}},{'depute_nom':1,'depute_shortid':1,'stats.positions.exprimes':1,'stats.votesamdements.pctpour':1}).sort([('stats.votesamdements.pctpour',-1)]).limit(20)])
    from fuzzywuzzy import fuzz
    sdesc = [(s['scrutin_dossier'],s['scrutin_dossierLibelle'],s['scrutin_desc'][20:]) for s in mdb.scrutins.find({'scrutin_dossier':{'$ne':'N/A'}},{'scrutin_dossier':1,'scrutin_dossierLibelle':1,'scrutin_desc':1,'_id':None})]
    r = []
    for s in mdb.scrutins.find({'scrutin_dossier':'N/A'},{'scrutin_desc':1,'_id':None,'scrutin_id':1}):
        for dos,doslib,d in sdesc:
            fz = fuzz.partial_ratio(s['scrutin_desc'][20:],d)
            if fz>97:
                r.append((s['scrutin_id'],dos,doslib))
                break

    return json_util.dumps(r)
    return json_util.dumps([(d['depute_shortid'],d['depute_suppleant'],d['depute_mandat_fin']) for d in mdb.deputes.find({'depute_actif':False})])
    return json_util.dumps(list(mdb.amendements.find({'sort':u"Adopt\u00e9","signataires_groupes":{'$elemMatch':{'$eq':'FI'}}},{'_id':None,'numInit':1,'numAmend':1})))


if __name__ == "__main__":

    app.run(debug=True)
