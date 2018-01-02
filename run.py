# -*- coding: utf-8 -*-

from obsapis import app,mdb,mdbrw
from flask import render_template
from bson import json_util
import xmltodict
import requests
import re

from obsapis.tools import json_response,xls_response,dictToXls,dictToXlsx
from obsapis.controllers.admin.imports.documents import importdocs
from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte
from obsapis.controllers.admin.updates.deputes import updateDeputesContacts
from obsapis.controllers.admin.imports.liensdossierstextes import import_liendossierstextes

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

@app.route('/test')
def test():
    return json_response(mdb.scrutins.find_one())
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'depute':'$depute'}
    pipeline = [{'$match':{'name':'visuelstat'}},{'$group':pgroup}]
    vdeps = []
    for g in mdb.logs.aggregate(pipeline):
        _g = g['_id']['depute']
        if _g != None:
            vdeps.append((_g,g['n']))

    return json_util.dumps(vdeps)

    #updateDeputesContacts()
    return json_util.dumps(mdb.deputes.find_one({'depute_shortid':'nicolelepeih'},{'depute_contacts':1,'_id':None}))
    #importdocs()
    #return json_util.dumps(list(mdb.logs.find({'name':'visuelstat'})))
    mts = list(mdb.scrutins.find({ '$text': { '$search': "rejet" } },{'scrutin_groupe':1,'scrutin_fulldesc':1,'scrutin_sort':1,'_id':None}))
    _mts = "\n".join([";".join([m.get('scrutin_groupe',''),m['scrutin_sort'],m['scrutin_fulldesc']]) for m in mts])
    print _mts

    return json_util.dumps(mdb.deputes.find_one({'depute_shortid':'thierrysolere'},{'stats':1,'_id':None}))
    return json_util.dumps(list(mdb.amendements.find({'numAmend':'311'})))
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
