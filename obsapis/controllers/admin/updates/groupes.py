# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne,TEXT
from obsapis.tools import strip_accents
import re

def createIndexes():
    mdbrw.groupes.ensure_index([("groupe_libelle", TEXT)],default_language='french')

def updateGroupesPresidents():
    for g in mdb.groupes.find({},{'groupe_abrev':1,'groupe_libelle':1,'groupe_membres':1,'_id':None}):
        president = [ m['uid'] for m in g['groupe_membres'] if m['actif']==True and m['qualite']==u'Président']
        president = mdb.deputes.find_one({'depute_uid':president[0]},{'_id':None,'depute_nom':1,'depute_shortid':1}) if president else None
        glibsa = strip_accents(g['groupe_libelle'])
        mdbrw.groupes.update_one({'groupe_abrev':g['groupe_abrev']},{'$set':{'groupe_libelle_sa':glibsa,'president':president}})
    return "ok"
def updateGroupesRanks():
    ops = []
    ranks = {}
    out = []
    from random import shuffle
    gpactifs = list(mdb.groupes.find({'groupe_abrev':{'$nin':['LC','NI']}}))
    rnombres = range(len(gpactifs))
    shuffle(rnombres)
    for i,gp in enumerate(gpactifs):

        for stat in ['nbitvs','nbmots']:
            ranks[stat] = ranks.get(stat,[]) + [ (gp['groupe_abrev'],(gp['stats'][stat],gp['stats'][stat]))  ]

        # stats commissions
        ranks['pctcommissions'] = ranks.get('pctcommissions',[]) + [ (gp['groupe_abrev'],(gp['stats']['commissions']['toutes']['present'],gp['stats']['commissions']['toutes']['present']) if 'commissions' in gp['stats'].keys() else (None,None)) ]
        # stats amendements
        ranks['nbamendements'] = ranks.get('nbamendements',[]) + [ (gp['groupe_abrev'],(gp['stats']['amendements']['rediges'],gp['stats']['amendements']['rediges']) if 'amendements' in gp['stats'].keys() else (None,None)) ]
        ranks['pctamendements'] = ranks.get('pctamendements',[]) + [ (gp['groupe_abrev'],(gp['stats']['amendements']['adoptes'],gp['stats']['amendements']['adoptes']) if 'amendements' in gp['stats'].keys() and 'adoptes' in gp['stats']['amendements'].keys() else (None,None)) ]
        for stat,val in gp['stats']['positions'].iteritems():
            ranks[stat] = ranks.get(stat,[]) + [ (gp['groupe_abrev'],(val,val))]
        if 'compat' in gp['stats'].keys():
            for stat,val in gp['stats']['compat'].iteritems():
                ranks['compat'+stat] = ranks.get('compat'+stat,[]) + [ (gp['groupe_abrev'],(val,val))]
    topflop = {}
    for rank in ranks.keys():
        topflop[rank] = {'down':{},'up':{}}
        topflop[rank]['down'] = sorted(ranks[rank],key=lambda x:x[1][0] if not x[1][0] in ('N/A',None) else -1, reverse=True)
        topflop[rank]['up'] = sorted(ranks[rank],key=lambda x:x[1][0] if not x[1][0] in ('N/A',None) else 'ZZZZ')
        topflop[rank]['down'] = dict([ (r[0],i+1) for i,r in enumerate(topflop[rank]['down']) ])
        topflop[rank]['up'] = dict([ (r[0],i+1) for i,r in enumerate(topflop[rank]['up']) ])

    for i,gp in enumerate(gpactifs):
        gp_ranks = {'down': dict((stat,topflop[stat]['down'].get(gp['groupe_abrev'],None)) for stat in topflop.keys()),
                     'up': dict((stat,topflop[stat]['up'].get(gp['groupe_abrev'],None)) for stat in topflop.keys())}

        ops.append(UpdateOne({'groupe_abrev':gp['groupe_abrev']},{'$set':{'stats.ranks':gp_ranks,'stats.hasard': rnombres[i]}}))
    if ops:
        mdbrw.groupes.bulk_write(ops)
    return "ok"
