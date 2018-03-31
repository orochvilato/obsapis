# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from obsapis.tools import normalize
from pymongo import UpdateOne
import requests
import re

def import_liendossierstextes():
    docsan = dict((d['numero'],d['doclien']) for d in mdb.documentsan.find({},{'numero':1,'doclien':1,'_id':None}))
    from stripogram import html2text, html2safehtml
    def getDossier(url):
        ops = []
        r = requests.get(url)
        texte = "NOPE"
        doc  = html2text(r.content,page_width=10000).decode('iso8859-1').split(u'\n\n')
        for i,l in enumerate(doc):
            l = l.replace(u'1ère',u'première').replace(u'2e ',u'deuxième ')
            #print l
            search = False
            if l[0:21]==u'Assemblée nationale -':
                if l[22:38]==u'première lecture' or l[22:38]==u'Nouvelle lecture':
                    _l = l[39:]
                    j = 0
                    while not (u"proposition de loi" in _l.lower() or u'projet de loi' in _l.lower() or j>5):
                        j += 1
                        _l = doc[i+j].replace(u'1ère',u'première').replace(u'2e ',u'deuxième ')

                    texte = _l.split(u',')[0]
                else:
                    _l = l
                search = True
                lecture = u' '.join(l[22:].split(' ')[0:2])
            if l[0:21]==u'Travaux préparatoires':
                j = 0
                while not (u"proposition de résolution" in _l.lower() or j>5):
                    j += 1
                    _l = doc[i+j].replace(u'1ère',u'première')
                texte = _l.split(u',')[0]
                search = True
                lecture = ""
            if l[0:26]==u"Commission Mixte Paritaire":

                j = 0
                m = None

                while not m and j<=5:
                    j += 1
                    m = re.search(u"sous le n° ([0-9]+) +à l'Assemblée nationale",doc[i+j])
                n = m.groups()[0] if m else None
                if n and n in docsan.keys():
                    ops.append((texte,"texte de la commission mixte paritaire",docsan[num],num,docsan[n],n))
                    #print (texte,"",docsan[num])
            if search:
                m = re.search(u", *(TA|) +n *° *([0-9]+)[^\-]* *",_l)
                if m:
                    if m.groups()[0]=='TA':
                        num = "TA%04d" % int(m.groups()[1])
                    else:
                        num = m.groups()[1]
                    ops.append((texte,lecture,docsan[num],num))


                    #print (texte,lecture,docsan[num])
        return ops

    dossiers = {}
    #dos = 'http://www.assemblee-nationale.fr/15/dossiers/bonne_application_asile_europeen.asp'
    #dossiers[dos] = getDossier(dos)

    def reduire(txt):
        txt2 = txt.replace(u"  ",u" ")
        while len(txt2) != len(txt):
            t = txt2.replace(u"  ",u" ")
            txt = txt2
            txt2 = t
        return txt2


    for dos in mdb.scrutins.distinct('scrutin_liendossier'):
        if dos:
            dossiers[dos] = getDossier(dos)


    from fuzzywuzzy import fuzz
    #print dossiers
    ops = []
    filters = {'scrutin_liendossier':{'$ne':None}}
    #filters = {'scrutin_num':435}


    for s in mdb.scrutins.find(filters): #'scrutin_liendossier':{'$ne':None}
        #if not s['scrutin_num'] in (321,):
        #    continue
        score = 0
        found = None
        dos = s['scrutin_liendossier']
        desc = reduire(s['scrutin_desc'])
        pl = re.search(r"(projet de loi .*) \((.*)\)",desc)
        ttyp = 'projet de loi'
        if not pl:
            ttyp= 'proposition de loi'
            pl = re.search(r"(proposition de loi[ ,].*) \((.*)\)",desc)

        if not pl:
            ttyp='proposition de résolution'
            pl = re.search(u"(proposition de résolution .*)",desc)
        if pl:
            lib = pl.groups()[0].strip().lower()

            if len(pl.groups())>1:
                lec = pl.groups()[1].strip().lower().replace(u'1ère',u'première').replace(u'2e ',u'deuxième ')
            else:
                lec = ""

            if len(dossiers[dos])==1 and dossiers[dos][0][1].lower()==lec:
                found = dossiers[dos][0]
            else:
                for txt in dossiers[dos]:
                    if txt[1].lower()==lec and fuzz.token_set_ratio(lib.lower(),txt[0].split(',')[0].lower())>90:
                        score = 0
                        for subt in txt[0].lower().strip().split(','):
                            score += fuzz.token_set_ratio(subt,lib)

                        if score>90:
                            found = txt
                            break

            #if found and u"texte de la commission paritaire" in desc:

            #    ttyp = "texte de la commission paritaire"
        print s['scrutin_num'],found
        if found:
            repl = [(ttyp,found[2],found[3])]
            if lec==u'texte de la commission mixte paritaire':
                repl.append((lec,found[4],found[5]))

            ops.append(UpdateOne({'scrutin_num':s['scrutin_num']},{'$set':{'scrutin_lientexte':repl}}))

        if not found:
            print "NOT FOUND",s['scrutin_num']
            #print "---------------------------\n-->",s['scrutin_desc']
            #print dossiers.get(dos,None)


    if ops:
        print "go"
        mdbrw.scrutins.bulk_write(ops)
        print "fin"
    return "ok"
