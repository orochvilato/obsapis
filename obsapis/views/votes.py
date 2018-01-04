from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

from obsapis.controllers.scrutins import getScrutinsData


@app.route('/votes')
@cache_function(expires=cache_pages_delay)
def votes():
    scrutins_data = use_cache('scrutins_data_new',lambda:getScrutinsData(),expires=300)
    nb = int(request.args.get('itemsperpage','25'))
    page = int(request.args.get('page','1'))-1
    groupe = request.args.get('groupe',request.args.get('group',None))
    search = request.args.get('requete',request.args.get('query',''))
    scrutingroupe = request.args.get('scrutingroupe',None)

    scrutin = request.args.get('scrutin',None)
    csp = request.args.get('csp',None)
    age = request.args.get('age',None)
    region = request.args.get('region',None)
    depute = request.args.get('depute',None)
    position = request.args.get('position',None)
    dissidence = int(request.args.get('dissidence','0'))
    skip = nb*page
    filters = []
    if scrutingroupe:
        filters.append({'scrutin_groupe':scrutingroupe})
    if dissidence:
        filters.append({'vote_dissident':True})
    if position:
        filters.append({'vote_position':position})
    if depute:
        filters.append({'depute_shortid': depute})
    if csp:
        filters.append({'depute_csp':csp})
    if age:
        filters.append({'depute_classeage':age})
    if groupe:
        filters.append({'groupe_abrev':groupe})
    if region:
        filters.append({'depute_region':region})
    if scrutin:
        try:
            scrutin=int(scrutin)
        except:
            pass
        filters.append({'scrutin_num':scrutin})
    if search:
        filters.append({'$text':{'$search':search}})
    if len(filters)==0:
        vote_filter = {}
    elif len(filters)==1:
        vote_filter = filters[0]
    else:
        vote_filter = {'$and':filters}

    votes = []
    import re
    for v in mdb.votes.find(vote_filter).sort('scrutin_num',-1).skip(skip).limit(nb):
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
