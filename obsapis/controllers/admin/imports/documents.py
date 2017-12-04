from obsapis import mdbrw
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
                    if r:
                        r = r.groups()
                        sublinks = doc.xpath('ul/li/a/@href')#.extract()
                        if sublinks:
                            docs.append(dict(numero=(url[2] % int(r[1])).upper(),titre=r[0],document=sublinks[1],dossier=sublinks[0]))

            offset += nb
    for d in docs:
        ops.append(UpdateOne({'numero':d['numero']},{'$set':d},upsert=True))
    if ops:
        mdbrw.documentsan.bulk_write(ops)
