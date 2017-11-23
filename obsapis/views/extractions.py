from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import json_response,cache_function,dictToXls,xls_response
import re
import datetime
import openpyxl
from obsapis.config import cache_pages_delay


@app.route('/extractions/contacts')
@cache_function(expires=0) #cache_pages_delay)
def contacts():
    tab = []
    for d in mdb.deputes.find({},{'_id':None,'depute_shortid':1,'depute_nom':1,'depute_contacts':1}):
        item = dict(id=d['depute_shortid'],nom=d['depute_nom'],twitter='',facebook='')
        for c in d['depute_contacts']:
            if c['type']=='twitter':
                item['twitter']=c['lien']
            elif c['type']=='facebook':
                item['facebook']=c['lien']
        tab.append(item)
    v = dictToXls(data={'sheets':['contacts'],'data':{'contacts':{'fields':['id','nom','twitter','facebook'],'data':tab}}})
    return xls_response('contactsDeputes',v)
