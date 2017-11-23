from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay

@app.route('/commissions/presences')
@cache_function(expires=cache_pages_delay)
def presences():

    depute = request.args.get('depute',None)
    commission = request.args.get('commission',None)
    page = int(request.args.get('page','1'))-1

    nb = int(request.args.get('itemsperpage','25'))
    groupe = request.args.get('groupe',request.args.get('group',None))
    skip = nb*page
    filters = []
    if depute:
        filters.append({'depute_shortid': depute})
    if groupe:
        filters.append({'groupe_abrev':groupe})
    if commission:
        filters.append({'commission_sid':commission})
    if len(filters)==0:
        com_filter = {}
    elif len(filters)==1:
        com_filter = filters[0]
    else:
        com_filter = {'$and':filters}

    prescom = list(mdb.presences.find(com_filter).sort([('presence_date',-1)]).skip(skip).limit(nb))

    def countItems():
        rcount = mdb.prescom.find(com_filter).count()
        return {'totalitems':rcount}
    cachekey= u"com%s_%s_%s" % (depute,groupe,commission)
    counts = use_cache(cachekey,lambda:countItems(),expires=3600)

    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(prescom),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=prescom,**counts)
    return json_response(result)
