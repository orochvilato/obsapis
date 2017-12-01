from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay


@app.route('/interventions/derniere')
@cache_function(expires=cache_pages_delay)
def interventions_last():
    itvs = list(mdb.interventions.find({'$and':[{'itv_president':False},{'depute_shortid':{'$ne':None}}]}).sort([('itv_date',-1),('session_id',-1),('itv_n',-1)]).limit(1))
    return json_response(itvs)

@app.route('/interventions')
@cache_function(expires=cache_pages_delay)
def interventions():
    nb = int(request.args.get('itemsperpage','25'))

    page = int(request.args.get('page','1'))-1
    groupe = request.args.get('groupe',request.args.get('group',None))
    search = request.args.get('requete',request.args.get('query',''))
    depute = request.args.get('depute',None)
    session = request.args.get('session',None)
    date = request.args.get('date',None)
    skip = nb*page
    filters = []
    if depute:
        filters.append({'depute_shortid': depute})
    if groupe:
        filters.append({'groupe_abrev':groupe})
    if session:
        filters.append({'session_id':session})
    if date:
        filters.append({'itv_date':date})
    if search:
        filters.append({'$text':{'$search':search}})

    if len(filters)==0:
        itv_filter = {}
    elif len(filters)==1:
        itv_filter = filters[0]
    else:
        itv_filter = {'$and':filters}

    itvs = list(mdb.interventions.find(itv_filter).sort([('itv_date',-1),('session_id',1),('itv_n',1)]).skip(skip).limit(nb))

    def countItems():
        rcount = mdb.interventions.find(itv_filter).count()
        return {'totalitems':rcount}
    cachekey= u"itv%s_%s_%s_%s_%s" % (depute,groupe,search,session,date)
    counts = use_cache(cachekey,lambda:countItems(),expires=3600)
    regx = re.compile(search, re.IGNORECASE)

    if search:
        for itv in itvs:
            repl = regx.subn('<strong>'+search+'</strong>',itv['itv_contenu'])
            if repl[1]:
                itv['itv_contenu'] = repl[0]

    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(itvs),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=itvs,**counts)
    return json_response(result)
