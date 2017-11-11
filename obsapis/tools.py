from flask import Response,request
from bson import json_util
from obsapis import use_cache
def json_response(r):
    resp = Response(json_util.dumps(r))
    resp.headers['Content-Type'] = 'text/json'
    return resp


def cache_function(expires=0):
    def wrap(f):
        def wrapped_f(*args,**kwargs):
            return use_cache(request.url,lambda:f(*args,**kwargs),expires=expires)
        return wrapped_f
    return wrap
