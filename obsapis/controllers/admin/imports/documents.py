# -*- coding: utf-8 -*-
import datetime
from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import ReplaceOne,TEXT,ASCENDING
import requests
import re
x="""<meta name="TITRE" content="sur le burnout visant à faire reconnaître comme maladies professionnelles les pathologies psychiques résultant de lépuisement professionnel ">
                        <meta name="ORIGINE_DOCUMENT" content="Assemblée nationale">
                        <meta name="LEGISLATURE_SESSION" content="15ème législature">
                        <meta name="TYPE_DOCUMENT" content="Proposition de loi">
                        <meta name="INTITULE_CLASSE_ESPECE" content="proposition de loi">
                        <meta name="TEXTE_ADOPTE" content="N">
                        <meta name="TITRE_DOSSIER" content="Questions sociales et santé : reconnaissance comme maladies professionnelles des pathologies psychiques résultant de lépuisement professionnel">
                        <meta name="NUMERO_DOCUMENT" content="516">
                        <meta name="DOCUMENT_DISTRIBUE" content="O">
                        <meta name="DATE_DEPOT" content="20/12/2017">
                        <meta name="DATE_PUBLICATION" content="29/12/2017">
                        <meta name="URL_DOSSIER" content="/15/dossiers/reconnaissance_epuisement_professionnel_maladie.asp">
                        <meta name="PROJET_LOI_FINANCE" content="N">
                        <meta name="DATE_LIGNE" content="27-12-2017 12:00">
                        <meta name="AUTEUR" content="M. François Ruffin  Auteur,M. Adrien Quatennens  Cosignataire,Mme Clémentine Autain  Cosignataire,M. Ugo Bernalicis  Cosignataire,M. Éric Coquerel  Cosignataire,M. Alexis Corbière  Cosignataire,Mme Caroline Fiat  Cosignataire,M. Bastien Lachaud  Cosignataire,M. Michel Larive  Cosignataire,M. Jean-Luc Mélenchon  Cosignataire,Mme Danièle Obono  Cosignataire,Mme Mathilde Panot  Cosignataire,M. Loïc Prud'homme  Cosignataire,M. Jean-Hugues Ratenon  Cosignataire,Mme Muriel Ressiguier  Cosignataire,Mme Sabine Rubin  Cosignataire,Mme Bénédicte Taurine  Cosignataire,La France insoumise Cosignataire">
                        <meta name="AUTEUR_ID" content="ID_722142">
                        <meta name="COSIGNATAIRE_ID" content="ID_720422;ID_588884;ID_720430;ID_721202;ID_721210;ID_720286;ID_720846;ID_718868;ID_2150;ID_721960;ID_720892;ID_719578;ID_721062;ID_719676;ID_721226;ID_718860;ID_GP_730958">
                        <meta name="AUTEUR_AFFICHAGE" content="M. François Ruffin ">
                        <meta name="URL_AUTEUR" content="/15/tribun/fiches_id/722142.asp">
                        <meta name="ACTEUR_RAPPORTEUR" content="N">
                        <meta name="COM_FOND_TXT" content="Commission des affaires sociales">
                        <meta name="ID_COM_FOND" content="ID_420120">"""


def importdocs():
    mdbrw.documentsan.ensure_index([("contenu", TEXT)],default_language='french')
    mdbrw.documentsan.ensure_index([("numero", ASCENDING)])

    nb = 500
    offset = 0
    docs = []
    ops = []
    ops_sigs = []
    urls = [('http://www2.assemblee-nationale.fr/documents/liste/(ajax)/1/(offset)/%d/(limit)/%d/(type)/depots/(legis)/15/(no_margin)/false',
            r'^(.+) - N[\xc2\xa0\xb0 ]+([0-9]+)$','%d'),
            ('http://www2.assemblee-nationale.fr/documents/liste/(ajax)/1/(offset)/%d/(limit)/%d/(type)/ta/(legis)/15/',
            r'(.*) N[^0-9]+([0-9]+)$','ta%04d')]

    for url in urls:
        offset = 0
        while 1:
            r = requests.get(url[0] % (offset,nb))
            from lxml import etree

            parser = etree.HTMLParser()
            page   = etree.fromstring(r.content, parser)

            doclinks = page.xpath('//ul[@class="liens-liste"]/li')

            if not doclinks:
                break
            for doc in doclinks:
                title = doc.xpath('h3/text()')
                if title:
                    r = re.match(url[1],title[0].replace('&nbsp;',' ').strip())
                    desc = doc.xpath('p/text()')
                    if desc:
                        desc = desc[0]
                    if r:
                        r = r.groups()
                        sublinks = doc.xpath('ul/li/a/@href')#.extract()
                        if len(sublinks)==2:
                            docs.append(dict(numero=(url[2] % int(r[1])).upper(),dossier=r[0],doclien='http://www2.assemblee-nationale.fr'+sublinks[1],dossierlien=sublinks[0],fulldesc=desc.replace(u'\u2018',"'").replace(u'\u0153',u'oe').replace(u'\u2019',"'").encode('iso8859-1').replace('\n','')))

            offset += nb
    deputes_id_gp = dict((d['depute_uid'][2:],{'id':d['depute_shortid'],'groupe':d['groupe_abrev']}) for d in mdb.deputes.find({},{'_id':None,'depute_shortid':1,'depute_uid':1,'groupe_abrev':1}))
    done = [ doc['numero'] for doc in mdb.documentsan.find({'contenu':{'$ne':None}},{'numero':1,'_id':None})]
    #done = []
    #print done
    items = ['TITRE','TYPE_DOCUMENT','TITRE_DOSSIER','NUMERO','DATE_DEPOT','URL_DOSSIER','AUTEUR','AUTEUR_ID','COSIGNATAIRE_ID','ID_COM_FOND']

    for d in docs:
        if d['numero'] in done:
            pass
            continue

        r = requests.get(d['doclien'])


        from lxml import etree
        parser = etree.HTMLParser()
        page   = etree.fromstring(r.content, parser)
        meta = {}
        for item in items:
            x = page.xpath('//meta[@name="%s"]/@content' % item)
            meta[item] = x[0] if x else ''


        auteurs = [ deputes_id_gp[a[3:]] for a in meta['AUTEUR_ID'].split(';') if a[3:] in deputes_id_gp.keys() ]
        cosignataires = [ deputes_id_gp[a[3:]] for a in meta['COSIGNATAIRE_ID'].split(';') if a[3:] in deputes_id_gp.keys() ]
        if not auteurs:
            auteurs = [{'id':'Gouvernement'}]
        d['auteurs'] = auteurs
        d['cosignataires'] = cosignataires
        d['titre'] = meta['TITRE']
        d['type'] = meta['TYPE_DOCUMENT']
        d['typeid'] = normalize(unicode(meta['TYPE_DOCUMENT']))
        d['dossier'] = meta['TITRE_DOSSIER']
        if meta['DATE_DEPOT']:
            d['date'] = datetime.datetime.strptime(meta['DATE_DEPOT'],'%d/%m/%Y')
        d['dossierlien'] = 'http://www.assemblee-nationale.fr'+meta['URL_DOSSIER']

        contenu = ' '.join(page.xpath('//p//text()')).replace('\n',' ').replace(u'\x0a',' ').replace(u'\x0e',' ').strip()
        if contenu:
            d['contenu'] = contenu
            print d['numero'],'OK'
        else:
            print d['numero'],len(contenu),d['typeid'],d['titre']

        mdbrw.documentsan.replace_one({'numero':d['numero']},d,upsert=True)
        #ops.append(ReplaceOne({'numero':d['numero']},d,upsert=True))
    if ops:
        mdbrw.documentsan.bulk_write(ops)
    #if ops_sigs:
    #    mdbrw.documentsan_signataires.bulk_write(ops_sigs)
