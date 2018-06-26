# -*- coding: utf-8 -*-

from obsapis import mdbrw,mdb
from pymongo import UpdateOne


def update_amendements():
    ops = []
    #return "ok"
    pgroup = {'n':{'$sum':1}}
    pgroup['_id'] = {'depute':'$auteurs.id'}
    pgroup['_id']['sort'] ='$sort'
    pipeline = [{'$match':{}},  {'$unwind':'$auteurs'},  {"$group": pgroup }] #'scrutin_typedetail':'amendement'

    stat_amdts = {}
    for amdt in mdb.amendements.aggregate(pipeline):
        amd = amdt['_id']
        if not amd['depute'] in stat_amdts.keys():
            stat_amdts[amd['depute']] = {'rediges':0,'adoptes':0,'cosignes':0}
        if amd['sort']==u'Adopté':
            stat_amdts[amd['depute']]['adoptes'] += amdt['n']
        stat_amdts[amd['depute']]['rediges'] += amdt['n']

    # TODO : stat GVT et commissions ?

    for d,stat in stat_amdts.iteritems():
        ops.append(UpdateOne({'depute_shortid':d},{'$set':{'depute_amendements':stat}}))
    if ops:
        mdbrw.deputes.bulk_write(ops)

from obsapis.controllers.admin.imports.amendements import get_signataires
def corrige_nonrenseignes():
    for amd in mdb.amendements.find({'$and':[{'sort':u'Non renseign\xe9'},{'_vu':{'$ne':True}}]}):
    #for amd in mdb.amendements.find({'sort':u'Non renseign\xe9'},{'id':1,'urlAmend':1}):

        meta = get_signataires(amd['urlAmend'])
        upd = {'_vu':True}
        if meta['SORT']!="":
            upd['sort'] = meta['SORT']
            #print amd['id'],meta['SORT']
            mdbrw.travaux.update_many({'idori':amd['id']},{'$set':{'sort':meta['SORT']}})
        mdbrw.amendements.update_one({'id':amd['id']},{'$set':upd})

def gendupamd():

    items={}

    for a in mdb.amendements.find({'sort':{'$ne':'Irrecevable'},'duplicate':{'$eq':None}},{'_id':None,'numInit':1,'designationArticle':1,'urlTexteRef':1}).sort([("numInit",1),("designationArticle",1)]):
        txt = a['numInit']
        art = a['designationArticle']
        if not txt in items.keys():
            items[txt] = {}

        items[txt][art] = a['urlTexteRef']


    def remove_html_tags(text):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    from fuzzywuzzy import fuzz
    dups  = {}
    counts = {}
    ptxt = 0
    print len(items.keys())
    for txt in sorted(items.keys()):
        counts[txt] = 0
        for art in sorted(items[txt].keys()):
            mdbrw.dupamd.remove({'numInit':txt,'designationArticle':art})
            
            counts[(txt,art)] = 0

            contents = []

            for amd in mdb.amendements.find({'sort':{'$ne':'Irrecevable'},'numInit':txt,'designationArticle':art},{'_id':None,'id':1,'dispositif':1,'auteurs':1,'urlAmend':1,'numAmend':1,'urlTexteRef':1}):
                text = remove_html_tags(amd['dispositif'])

                contents.append(dict(doc=txt,auteur=amd['auteurs'][0],art=art,id=amd['id'],num=amd['numAmend'],url=amd['urlAmend'],texturl=amd['urlTexteRef'],content=text))

            if not txt in dups.keys():
                dups[txt] = {}
            if not art in dups[txt].keys():
                dups[txt][art] = []

            x = range(len(contents))

            while x:
                item=contents[x[0]]['content']
                matches = [x[0]]
                for cmp in x[1:]:
                    if fuzz.ratio(item,contents[cmp]['content'])>90:
                        matches.append(cmp)
                if len(matches)>1:
                    mtchs = []
                    for m in matches:
                        v = contents[m]
                        v['duplicate'] = True
                        mtchs.append(dict(id=v['id'],auteur=v['auteur'],num=v['num'],url=v['url']))
                    dups[txt][art].append(mtchs)
                    counts[(txt,art)] += len(matches)
                    counts[txt] += len(matches)
                x = [e for e in x if not e in matches]



            for dup in dups[txt][art]:
                id = mdbrw.dupamd.insert({'id':dup[0]['id'],'numInit':txt,'designationArticle':art})
                for d in dup:
                    mdbrw.amendements.update({'id':d['id']},{'$set':{'duplicate':id}})
            for c in contents:
                if not c.get('duplicate',False):
                    mdbrw.amendements.update({'id':c['id']},{'$set':{'duplicate':False}})


    return "ok"
