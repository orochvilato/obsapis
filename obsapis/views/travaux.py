# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function
import re
import datetime

from obsapis.config import cache_pages_delay


@app.route('/travaux')
@cache_function(expires=cache_pages_delay)
def view_travaux():
    amd_sorts = {'retire':u'Retiré', 'tombe':u'Tombé','adopte':u'Adopté','rejete':u'Rejeté','nonsoutenu':u'Non soutenu','nonrenseigne':u'Non renseigné'}
    nb = int(request.args.get('itemsperpage','25'))
    page = int(request.args.get('page','1'))-1
    search = request.args.get('requete',request.args.get('query',''))
    depute = request.args.get('depute',None)
    groupe= request.args.get('groupe',None)
    cosig = request.args.get('cosignataire',None)
    sort = request.args.get('sort',None)
    ttype = request.args.get('type',None)
    asupp = request.args.get('suppression',None)

    skip = nb*page
    filters = []


    if 'suppression' in request.args.keys() and ttype=='amendement':
        filters.append({'suppression':(asupp!="")})
    if sort and ttype=='amendement' and sort in amd_sorts.keys():
        filters.append({'sort':amd_sorts[sort]})

    if depute:
        filters.append({'depute':depute})
        filters.append({'auteur':False if cosig else {'$in':[None,True]}})
    elif groupe:
        filters.append({'groupe':groupe})
    else:
        filters.append({'depute':None})

    if ttype=='question':
        filters.append({'type':{'$in':['QG','QE','QOSD']}})
    elif ttype=='amendement':
        filters.append({'type':'amendement'})
    elif ttype=='document':
        filters.append({'type':{'$nin':['QG','QE','QOSD','amendement']}})

    if search:
        search = '"'+search+'"'
        def searchText():
            txt_amd = [ a['id'] for a in mdb.amendements.find({'$text':{'$search':search}}) ]
            txt_que = [ q['id'] for q in mdb.questions.find({'$text':{'$search':search}}) ]
            txt_doc = [ d['id'] for d in mdb.documentsan.find({'$text':{'$search':search}}) ]
            return txt_amd+txt_que+txt_doc
        cachekey = u"trvtxt%s" % (search)
        ids = use_cache(cachekey,lambda:searchText(),expires=3600)
        filters.append({'idori':{'$in':ids}})

    def makefilter(f):
        if len(f)==0:
            mf = {}
        elif len(f)==1:
            mf = f[0]
        else:
            mf = {'$and':f}
        return mf


    tfilter = makefilter(filters)
    print filters,tfilter

    travaux = list(mdb.travaux.find(tfilter).sort('date',-1).skip(skip).limit(nb))

    def countItems():
        rcount = mdb.travaux.find(tfilter).count()
        return {'totalitems':rcount}
    cachekey= u"trv%s_%s_%s_%s_%s_%s" % (depute,groupe,search,ttype,sort,cosig)
    counts = use_cache(cachekey,lambda:countItems(),expires=3600)

    import math
    nbpages = int(math.ceil(float(counts['totalitems'])/nb))
    result = dict(nbitems=len(travaux),nbpages=nbpages, currentpage=1+page,itemsperpage=nb, items=travaux,**counts)
    return json_response(result)
