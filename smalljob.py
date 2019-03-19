# -*- coding: utf-8 -*-

from obsapis import jobs,mdb

jobs.stop_scheduler()
fields = [ u'depute_nom',u'groupe_abrev',u'scrutin_num',u'scrutin_date', u'vote_position',  u'vote_dissident',u'scrutin_groupe', u'scrutin_fulldesc', u'scrutin_dossierLibelle',u'scrutin_typeLibelle',  u'scrutin_typedetail']
votes = mdb.votes.find({'depute_departement':'Loire'},{ u'_id':None,u'scrutin_dossierLibelle':1,u'scrutin_typeLibelle':1,u'scrutin_groupe':1,u'groupe_abrev':1, u'vote_position':1, u'depute_nom':1,  u'scrutin_num':1, u'scrutin_date':1, u'vote_dissident':1, u'scrutin_typedetail':1, 'scrutin_fulldesc':1})

import csv

f = open('votesLoire.csv','wb')
f.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
w = csv.DictWriter(f,fields)
w.writeheader()
for V in votes:
    w.writerow({k:(v.encode('utf8') if isinstance(v,basestring) else v) for k,v in V.items() })
f.close()
