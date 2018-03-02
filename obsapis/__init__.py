# -*- coding: utf-8 -*-

import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
import pymongo
from bson import json_util

from config_private import mongo_read_user,mongo_read_password,mongo_write_user,mongo_write_password,smtp

client = pymongo.MongoClient('mongodb://%s:%s@observatoire-assemblee.orvdev.fr:27017/obsass' %(mongo_read_user,mongo_read_password))
mdb = client.obsass

clientrw = pymongo.MongoClient('mongodb://%s:%s@observatoire-assemblee.orvdev.fr:27017/obsass' %(mongo_write_user,mongo_write_password))
mdbrw = clientrw.obsass

from flask import Flask
from flask_cors import CORS
import os
obspath = '/'.join(os.path.abspath(__file__).split('/')[:-2])
app = Flask(__name__)
CORS(app)


import bmemcached
#memcache = bmemcached.Client(('observatoire-assemblee.orvdev.fr:11211',))
memcache = bmemcached.Client(('127.0.0.1:11211',))



def use_cache(k,fct,expires=60,compress=-1):
    k = k.encode('utf8')
    if expires==0:
        memcache.delete(k)
        v=None
    else:
        v = memcache.get(k)
    if not v:
        v = fct()
        if expires!=0:
            memcache.set(k,v,time=expires,compress_level=compress)
    else:
        pass
    return v

from views import deputes,votes,interventions,svgs,logs,scrutins,groupes,visuels,extractions,commissions,charts,admin,obsgouv,graphes,specifique,visuel,travaux

@app.route('/testerror')
def testerror():
    1/0

if 1: #enable_logging
    import logging
    from cStringIO import StringIO
    from logging.handlers import SMTPHandler
    from logging import StreamHandler,Formatter
    import os
    import inspect
    # os.path.realpath(__file__)

    class eaiHandler(StreamHandler):
        def emit(self,record):
            StreamHandler.emit(self,record)

    class eaiSMTPHandler(SMTPHandler):
        def getSubject(self,record):
            return "Erreur ObsAPI: %s (%s)" % (record.message,str(record.exc_info[:-1][1]))

    class eaiContextFilter(logging.Filter):
        def filter(self,record):
            #record.user = session['id']['username'] if 'id' in session else ''
            record.context = str(inspect.trace()[-1][0].f_locals)
            return True

    eai_handler = eaiHandler(StringIO())
    mail_handler = eaiSMTPHandler((smtp['host'],smtp['port']),
                               'api@observatoire-democratie.fr',
                               'observatoireapi@yahoo.com', 'Erreur ObsAPI',credentials=(smtp['username'],smtp['password']),secure=(None,None))

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Context:

%(context)s

Message:

%(message)s
'''))
    app.logger.addFilter(eaiContextFilter())
    app.logger.addHandler(mail_handler)
    app.logger.addHandler(eai_handler)


import jobs
jobs.start_scheduler()
