# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import UpdateOne
import requests
import re

def import_liendossierstextes():
    docsan = dict((d['numero'],d['document']) for d in mdb.documentsan.find({},{'numero':1,'document':1,'_id':None}))
    from stripogram import html2text, html2safehtml
    ops = []
    def getDossier(url):
        r = requests.get(url)
        texte = "NOPE"
        doc  = html2text(r.content,page_width=10000).decode('iso8859-1').split(u'\n\n')
        for i,l in enumerate(doc):
            l = l.replace(u'1ère',u'première')
            if l[0:21]==u'Assemblée nationale -':
                if l[22:]==u'première lecture':
                    texte = doc[i+1].split(',')[0]
                    _l = doc[i+1]

                else:
                    _l = l
                    if l[22:38]==u'première lecture':
                        texte = u' '.join(l[22:].split(' ')[2:])
                lecture = u' '.join(l[22:].split(' ')[0:2])

                m = re.search(u", *(TA|) +n *° *([0-9]+)[^\-]* *",_l)
                if m:
                    if m.groups()[0]=='TA':
                        num = "TA%04d" % int(m.groups()[1])
                    else:
                        num = m.groups()[1]
                    ops.append((texte,lecture,docsan[num]))
                    print (texte,lecture,docsan[num])


    for dos in mdb.scrutins.distinct('scrutin_liendossier'):
        if dos:
            print dos
            getDossier(dos)
    return ops
