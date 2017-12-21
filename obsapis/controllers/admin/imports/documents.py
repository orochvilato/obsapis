# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import UpdateOne
import requests
import re
def importdocs():
    #mdbrw.documentsan.remove()
    nb = 500
    offset = 0
    docs = []
    ops = []
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
                            docs.append(dict(numero=(url[2] % int(r[1])).upper(),titre=r[0],document='http://www2.assemblee-nationale.fr'+sublinks[1],dossier=sublinks[0],description=desc))

            offset += nb
    depute_shortids = mdb.deputes.distinct('depute_shortid')
    done = [ doc['numero'] for doc in mdb.documentsan.find({},{'numero':1,'_id':None})]
    for d in docs:
        if d['numero'] in done:
            pass
            #continue
        if d['description'][:18]==u'Proposition de loi':
            r = requests.get(d['document'])

            from lxml import etree
            parser = etree.HTMLParser()
            page   = etree.fromstring(r.content, parser)

            deputes = []
            print "----",d['numero'],"----"
            #p = page.xpath(u'//p[text()[contains(.,"présentée par")]]/following-sibling::p/text()')
            p = page.xpath(u'//p/text()')
            if p and u'd\xe9put\xe9' in ''.join(p):
                noms = []
                start = False
                for i,_p in enumerate(p):
                    print i,_p
                    if u"d\xe9put\xe9" in _p:
                        break

                    if start:
                        noms.append(_p)
                    if u"pr\xe9sent\xe9e par" in _p or ((i>0) and u"pr\xe9sent\xe9e par" in p[i-1]+p[i]):
                        start = True

                noms = ' '.join(noms)
                print "-->", noms
                p = noms.replace(' et ',',').replace(u'\xa0',' ').replace('MM. ','').replace('M. ','').replace('Mme ','')
                print p
                for dep in p.split(','):
                    norm = normalize(unicode(dep))
                    if norm in depute_shortids:
                        deputes.append(norm)
                    else:
                        pass
                        #print dep,norm,p

                d['signataires'] = deputes
                d['type'] = 'propositionloi'

        ops.append(UpdateOne({'numero':d['numero']},{'$set':d},upsert=True))
    if ops:
        mdbrw.documentsan.bulk_write(ops)
