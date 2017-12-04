# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

from obsapis.config import cache_pages_delay

from obsapis.controllers.admin.imports.documents import importdocs
from obsapis.controllers.admin.updates.scrutins import updateScrutinsTexte

@app.route('/admin/updateScrutinsRefs'):
def updateScrutinsRefs():
    importdocs()
    updateScrutinsTexte()

#@app.route('/charts/participationgroupes')
#def votesgroupes():
