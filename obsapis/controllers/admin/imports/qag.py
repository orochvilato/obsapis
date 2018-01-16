# -*- coding: utf-8 -*-

import datetime
from obsapis import mdbrw,mdb
from obsapis.tools import normalize, json_response
from pymongo import ReplaceOne,TEXT,ASCENDING
import requests
import datetime
import re
from lxml import etree

from string import Template
def parse_content(content):
    from lxml import etree
    parser = etree.HTMLParser()
    page   = etree.fromstring(content, parser)
    return page


def import_qag():
    legislature = 15
    mdbrw.questions.ensure_index([("contenu", TEXT)],default_language='french')
    mdbrw.questions.ensure_index([("id", ASCENDING)])
    def parse_question(url):
        def parse_item(txt):
            return ''.join(page.xpath('//*[span/text()[contains(.,"%s")]]/text()' % txt)).replace('\n','').strip()
        r = requests.get(url)
        numero,qtype = re.search(r'[0-9][0-9]-([0-9]+)([A-Z]+)',url).groups()
        id = url.split('/')[-1].split('.')[0]
        page = parse_content(r.content)
        depute = page.xpath('//a[contains(@title,"Lien vers la fiche")]/@href')[0].split('/')[-1][4:]
        min_inter = parse_item(u'Ministère interrogé')
        min_attri = parse_item(u'Ministère attributaire')
        rubrique = parse_item(u'Rubrique')
        titre = parse_item(u'Titre')
        datejo = page.xpath(u'//div[text()[contains(.,"Question publiée au JO")]]/span/text()')[0]

        question = page.xpath(u'//div[h3/text()[contains(.,"Texte de la question")]]/p/text()')[0].strip()
        reponse = " ".join(page.xpath(u'//div[@class="reponse_contenu"]//text()')).replace('\n',' ').strip()
        if u'\xcatre alert\xe9(e) de la r\xe9ponse' in reponse:
            reponse = ""
        return dict(id=id,
                    url = url,
                    type=qtype,
                    numero=numero,
                    depute=depsid[depute]['id'],
                    groupe=depsid[depute]['g'],
                    ministere_interroge=min_inter,
                    ministere_attributaire=min_attri,
                    legislature=legislature,
                    rubrique = rubrique,
                    titre = titre,
                    date = datetime.datetime.strptime(datejo,'%d/%m/%Y'),
                    contenu = question+ ' ' + reponse,
                    )

    depsid = dict((d['depute_uid'],{'id':d['depute_shortid'],'g':d['groupe_abrev']}) for d in mdb.deputes.find({},{'depute_uid':1,'groupe_abrev':1,'depute_shortid':1,'_id':None}))
    s = requests.Session()
    dejavu = [ q['url'] for q in mdb.questions.find({},{'url':1,'_id':0})]

    nbitems = 1000

    #return json_response(parse_question('http://questions.assemblee-nationale.fr/q15/15-395QG.htm'))

    r = s.post('http://www2.assemblee-nationale.fr/recherche/resultats_questions',data={'limit':nbitems,'legislature':legislature})

    page = parse_content(r.content)
    questions = page.xpath('//section//article//tbody//td/a/@href')
    code = page.xpath('//li/a[span/text()[contains(.,"Suivant")]]/@href')[0].split('/')[-1]
    offset = 0
    while questions:
        ops = []
        #print len(questions)
        for qurl in questions:
            if not qurl in dejavu:
                q = parse_question(qurl)
                q['legislature'] = legislature
                ops.append(ReplaceOne({'id':q['id']},q,upsert=True))
        if ops:
            mdbrw.questions.bulk_write(ops)
        offset += nbitems
        r = s.get('http://www2.assemblee-nationale.fr/recherche/resultats_questions/%d/(offset)/%d/(query)/%s' % (legislature,offset,code))
        page = parse_content(r.content)
        questions = page.xpath('//section//article//tbody//td/a/@href')
    return "ok"
