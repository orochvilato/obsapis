#!/home/www-data/web2py/applications/observatoireassemblee/.pyenv/bin/python
# -*- coding: utf-8 -*-
# args :
# outputpath
# lexiquespath
# exclude

import scrapy
import requests
import json
import re
import xmltodict
from fuzzywuzzy import fuzz
from scrapy.crawler import CrawlerProcess
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

import sys

output_path = sys.argv[1]



import unicodedata
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
def normalize(s):
    return strip_accents(s).replace(u'\u2019','').replace('&apos;','').replace(u'\xa0','').encode('utf8').replace(' ','').replace("'",'').replace('-','').replace('\x0a','').replace('\xc5\x93','oe').decode('utf8').lower() if s else s


collabs = []


class HATVPSpider(scrapy.Spider):
    name = "HATVP"
    base_url = 'http://www.hatvp.fr'
    start_url = base_url+'/resultat-de-recherche-avancee/?document=&mandat=depute&region=0&dep='
    def start_requests(self):
        urls = [ self.start_url]


        for url in urls:
            request = scrapy.Request(url=url, callback=self.parse_main)
            yield request



    def parse_main(self, response):
        for fiche in response.xpath('//aside[@class="list-results"]/ul/li//p[@class="title"]/a/@href'):
            url = fiche.extract()
            request = scrapy.Request(url=url, callback=self.parse_fiche)
            request.meta['url'] = url
            yield request
            #break

    def parse_fiche(self, response):

        #print response.xpath('//header[@class="person"]/div[@class="title"]/h3/text()').extract()
        depid = normalize(response.xpath('//header[@class="person"]/div[@class="title"]/h3/text()').extract()[0][1:].strip())

        for collab in response.xpath('//div[p[text()[contains(.,"collaborateurs parlementaires")]]]/div/p/text()').extract():
            m = re.match(r' :\n +(.*) +',collab)
            if m:
                collab = m.groups()[0].strip()
                collabs.append([depid,collab])

        for h in response.xpath('//aside[contains(@class,"table-historique")]//a[contains(@class,"dl-declaration-history") and contains(@href,".xml")]/@href').extract():
            r = requests.get(h)
            xml = xmltodict.parse(r.content)
            _x = xml['declaration']['activCollaborateursDto']
            if _x.get('items',None):
                if _x['items']:
                    if isinstance(_x['items']['items'],list):
                        for _col in _x['items']['items']:
                            if not [depid,_col['nom']] in collabs:
                                collabs.append([depid,_col['nom']+' (anciennement)'])
                    else:
                        _col = _x['items']['items']
                        if not [depid,_col['nom']] in collabs:
                            collabs.append([depid,_col['nom']+' (anciennement)'])



process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)','DOWNLOAD_DELAY':0.25
})

process.crawl(HATVPSpider)
process.start() # the script will block here until the crawling is finished

    #runner = CrawlerRunner({
    #    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)','DOWNLOAD_DELAY':0.25
    #})

    #d = runner.crawl(HATVPSpider)
    #d.addBoth(lambda _: reactor.stop())
    #reactor.run()



col_dep = {}
for _col in collabs:
    dep,col = _col
    if not dep in col_dep.keys():
        col_dep[dep] = []
    col_dep[dep].append(col)
ops = []
for dep in col_dep.keys():
    col_dep[dep] = list(set(col_dep[dep]))

import json
with open(output_path+'/hatvp.json','w') as f:
    f.write(json.dumps(col_dep))
