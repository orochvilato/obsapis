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
from obsapis.controllers.admin.updates.deputes import updateDeputesContacts

@app.route('/admin/updateScrutinsRefs')
def view_updateScrutinsRefs():
    importdocs()
    updateScrutinsTexte()
    return "ok"

@app.route('/admin/updateDeputesContacts')
def view_updateDeputesContacts():
    return json_response(updateDeputesContacts())
#@app.route('/charts/participationgroupes')
#def votesgroupes():
