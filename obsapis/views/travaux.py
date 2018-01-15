from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay


@app.route('/amendements')
@cache_function(expires=cache_pages_delay)
def view_amendements():
    amd_sorts = {'retire':u'Retiré', 'tombe':u'Tombé','adopte':u'Adopté','rejete':u'Rejeté','nonsoutenu':u'Non soutenu','nonrenseigne':u'Non renseigné'}
    nb = int(request.args.get('itemsperpage','25'))
    page = int(request.args.get('page','1'))-1
    search = request.args.get('requete',request.args.get('query',''))
    depute = request.args.get('depute',None)
    role = request.args.get('role',None)
    sort = request.args.get('sort',None)
    skip = nb*page
    filters = []
    if sort and sort in amd_sorts.keys():
        filters.append({'sort':amd_sorts[sort]})
    if depute:
        fdep = []
        if not role or role=='auteur':
            fdep.append({'auteur':depute})
        if not role or role=='cosignataire':
            fdep.append({'signataires_ids': auteur})
        if len(fdep)>1:
            fdep = {'$and':fdep }
        if len(fdep)>0:
            filters.append(fdep)
    if search:
        filters.append({'$text':{'$search':search}})

    if len(filters)==0:
        amd_filter = {}
    elif len(filters)==1:
        amd_filter = filters[0]
    else:
        amd_filter = {'$and':filters}

    amdts = []

    for v in mdb.amendemens.find(amd_filter).sort('scrutin_num',-1).skip(skip).limit(nb):
        v['scrutin_sort'] = scrutins_data[v['scrutin_num']]['sort']
        if scrutins_data[v['scrutin_num']]['urlAmendement']:
            v['scrutin_desc'] = re.sub(r'([0-9]+)',r'<a target="_blank" href="'+scrutins_data[v['scrutin_num']]['urlAmendement']+r'">\1</a>',v['scrutin_desc'],1)
        for lien in scrutins_data[v['scrutin_num']]['scrutin_lientexte']:
            v['scrutin_desc'] = v['scrutin_desc'].replace(lien[0],'<a target="_blank" href="'+lien[1]+r'">'+lien[0]+'</a>')
        v['scrutin_dossierLibelle'] = v['scrutin_dossierLibelle'].replace(u'\u0092',"'") # pb apostrophe
        votes.append(v)

    def countItems():
        rcount = mdb.votes.find(vote_filter).count()
        return {'totalitems':rcount}
    cachekey= u"vot%s_%s_%s_%s_%s_%s_%s_%s_%s_%s" % (depute,position,scrutingroupe,dissidence,scrutin,age,csp if csp else csp,groupe,search,region if region else region)
    counts = use_cache(cachekey,lambda:countItems(),expires=3600)
    regx = re.compile(search, re.IGNORECASE)
    if search:
        for v in votes:
            repl = regx.subn('<strong>'+search+'</strong>',v['scrutin_desc'])
            if repl[1]:
                v['scrutin_desc'] = repl[0]

    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(votes),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=votes,**counts)
    return json_response(result)
