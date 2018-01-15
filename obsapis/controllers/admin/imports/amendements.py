# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import ReplaceOne,UpdateOne,TEXT,ASCENDING
import datetime
import json
import requests
import re

def get_signataires(url):
    items = ['AUTEUR_ID','COSIGNATAIRES_ID','DATE_BADAGE']
    r = requests.get(url)
    from lxml import etree
    parser = etree.HTMLParser()
    page   = etree.fromstring(r.content, parser)
    result = {}
    for item in items:
        x = page.xpath('//meta[@name="%s"]/@content' % item)
        result[item] = x[0] if x else ''

    return result
def import_amendements(rebuild=False):
    mdbrw.amendements.ensure_index([("dispositif", TEXT)],default_language='french')
    mdbrw.amendements.ensure_index([("id", ASCENDING)])
    mdbrw.amendements.reindex()
    leg = '15'
    from HTMLParser import HTMLParser
    html = HTMLParser()

    deputes_id_gp = dict((d['depute_uid'][2:],{'id':d['depute_shortid'],'groupe':d['groupe_abrev']}) for d in mdb.deputes.find({},{'_id':None,'depute_shortid':1,'depute_uid':1,'groupe_abrev':1}))

    from requests import Session
    deja_amd = dict((a['id'],a) for a in mdb.amendements.find({},{'id':1,'auteurs':1,'urlTexteRef':1,'_id':None}))

    sess = Session()
    r = sess.get('http://www2.assemblee-nationale.fr/recherche/amendements')

    nb = 1000
    count = 1000
    start = 1
    stats = {}
    stats_deps = {}
    notfound = []
    while (count==nb):
        r = sess.get('http://www2.assemblee-nationale.fr/recherche/query_amendements?typeDocument=amendement&leg=%s&idExamen=&idDossierLegislatif=&missionVisee=&numAmend=&idAuteur=&premierSignataire=false&idArticle=&idAlinea=&sort=&dateDebut=&dateFin=&periodeParlementaire=&texteRecherche=&rows=%d&format=json&tri=ordreTexteasc&start=%d&typeRes=liste' % (leg,nb,start))
        amds = r.json()
        fields = amds['infoGenerales']['description_schema'].split('|')
        count = len(amds[u'data_table'])
        start += nb
        op_amendements = []
        for i,a in enumerate(amds[u'data_table']):
            print i
            updt = False
            amd = dict((fields[i],_a) for i,_a in enumerate(a.split('|')))
            if not deja_amd.get(amd['id'],{}).get('auteurs',False):
                meta = get_signataires(amd['urlAmend'])
                auteurs = [ deputes_id_gp[_a] for _a in meta['AUTEUR_ID'].split(';') if _a in deputes_id_gp.keys() ]
                cosignataires = [ deputes_id_gp[_a] for _a in meta['COSIGNATAIRES_ID'].split(';') if _a in deputes_id_gp.keys() ]
                if not auteurs:
                    auteurs = [{'id':'Gouvernement'}]
                amd['auteurs'] = auteurs
                amd['cosignataires'] = cosignataires

                if meta['DATE_BADAGE']:
                    amd['date'] = datetime.datetime.strptime(meta['DATE_BADAGE'],'%d/%m/%Y')
                print "%d/%d" % (start-nb+i,len(amds[u'data_table']))
                updt = True
            if not deja_amd.get(amd['id'],{}).get('urlTexteRef',False):
                r = sess.get('http://www2.assemblee-nationale.fr/recherche/query_amendements?id=%s&leg=%s&typeRes=doc' % (amd['id'],leg))
                amd_json = json.loads(r.content)
                amfields = amd_json['infoGenerales']['description_schema'].split('|')
                amd_detail = dict((amfields[j],_amd) for j,_amd in enumerate(amd_json[u'data_table'][0].split('|')))
                amd.update(amd_detail)
                amd['legislature'] = int(leg)
                print start-nb+i,amd['id'],amd['urlTexteRef']
                updt = True

            if updt:
                mdbrw.amendements.replace_one({'id':amd['id']},amd,upsert=True)
                pass
                #op_amendements.append(ReplaceOne({'id':amd['id']},amd,upsert=True))

        if op_amendements:
            mdbrw.amendements.bulk_write(op_amendements)
            import re
            regx = re.compile("^<p[^>]*>Supprimer",)
            mdbrw.amendements.update_many({'$and':[{'suppression':None},{'dispositif':regx}]},{'$set':{'suppression':True}})

    return "ok"
