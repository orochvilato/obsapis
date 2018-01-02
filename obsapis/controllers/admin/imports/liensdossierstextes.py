# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import UpdateOne
import requests
import re

def import_liendossierstextes():
    docsan = dict((d['numero'],d['document']) for d in mdb.documentsan.find({},{'numero':1,'document':1,'_id':None}))
    from stripogram import html2text, html2safehtml
    def getDossier(url):
        ops = []
        r = requests.get(url)
        texte = "NOPE"
        doc  = html2text(r.content,page_width=10000).decode('iso8859-1').split(u'\n\n')
        for i,l in enumerate(doc):
            l = l.replace(u'1ère',u'première')
            #print l
            if l[0:21]==u'Assemblée nationale -':
                if l[22:38]==u'première lecture' or l[22:38]==u'Nouvelle lecture':
                    _l = l[39:]
                    j = 0
                    while not (u"proposition de loi" in _l.lower() or u'projet de loi' in _l.lower() or j>5):
                        j += 1
                        _l = doc[i+j].replace(u'1ère',u'première')

                    texte = _l.split(u',')[0]
                else:
                    _l = l

                lecture = u' '.join(l[22:].split(' ')[0:2])

                m = re.search(u", *(TA|) +n *° *([0-9]+)[^\-]* *",_l)
                if m:
                    if m.groups()[0]=='TA':
                        num = "TA%04d" % int(m.groups()[1])
                    else:
                        num = m.groups()[1]
                    ops.append((texte,lecture,docsan[num]))
                    #print (texte,lecture,docsan[num])
        return ops
    #getDossier('http://www.assemblee-nationale.fr/15/dossiers/loi_finances_2018.asp')
    #return "ok"
    def reduire(txt):
        txt2 = txt.replace(u"  ",u" ")
        while len(txt2) != len(txt):
            t = txt2.replace(u"  ",u" ")
            txt = txt2
            txt2 = t
        return txt2

    dossiers = {}
    for dos in mdb.scrutins.distinct('scrutin_liendossier'):
        if dos:
            dossiers[dos] = getDossier(dos)

    from fuzzywuzzy import fuzz

    ops = []
    for s in mdb.scrutins.find({'scrutin_liendossier':{'$ne':None}}):
        score = 0
        found = None
        dos = s['scrutin_liendossier']
        desc = reduire(s['scrutin_desc'])
        pl = re.search(r"(projet de loi .*) \((.*)\)",desc)
        ttyp = 'projet de loi'
        if not pl:
            ttyp= 'proposition de loi'
            pl = re.search(r"(proposition de loi .*) \((.*)\)",desc)
        if pl:
            lib = pl.groups()[0].strip().lower()
            lec = pl.groups()[1].strip().lower().replace(u'1ère',u'première')
            if len(dossiers[dos])==1 and dossiers[dos][0][1].lower()==lec:
                found = dossiers[dos][0]
            else:
                for txt in dossiers[dos]:
                    if txt[1].lower()==lec and fuzz.token_set_ratio(lib.lower(),txt[0].split(',')[0].lower())>97:
                        score = 0
                        for subt in txt[0].lower().strip().split(','):
                            score += fuzz.token_set_ratio(subt,lib)
                        if score>97:
                            found = txt
                            break
            #print lib,lec
        if found:
            ops.append(UpdateOne({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_lientexte':(ttyp,found[2])}}))

        if not found:
            print "---------------------------\n-->",s['scrutin_desc']
            print dossiers[dos]


    if ops:
        print "go"
        mdbrw.scrutins.bulk_write(ops)
        print "fin"
    return "ok"
