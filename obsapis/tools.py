from flask import Response,request
from bson import json_util
from obsapis import use_cache,mdbrw
import datetime


def json_response(r):
    resp = Response(json_util.dumps(r))
    resp.headers['Content-Type'] = 'text/json'
    return resp

from functools import wraps
def cache_function(expires=0):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args,**kwargs):
            return use_cache(request.url,lambda:f(*args,**kwargs),expires=expires)
        return wrapped_f
    return wrap

def logitem(name,item,fields):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args,**kwargs):
            log = dict((f,request.args.get(f)) for f in fields if request.args.get(f))
            log.update({ 'name':name,'timestamp':datetime.datetime.now(),'ip':request.environ['REMOTE_ADDR'],'user_agent':request.headers.get('User-Agent')})
            mdbrw.logs.insert_one(log)
            #print args,kwargs
            #print log
            return f(*args,**kwargs)
        return wrapped_f
    return wrap

def getdot(e,k):
    for _k in k.split('.'):
        if _k in e.keys():
            e = e[_k]
        else:
            e = ""
            break
    return e

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
def normalize(s):
    return strip_accents(s).replace(u'\u2019','').replace('&apos;','').replace(u'\xa0','').encode('utf8').replace(' ','').replace("'",'').replace('-','').replace('\x0a','').replace('\xc5\x93','oe').decode('utf8').lower() if s else s
