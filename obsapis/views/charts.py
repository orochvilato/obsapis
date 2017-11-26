# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

@app.route('/charts/pyramideage')
def pyramideage():
    #return json_response(mdb.deputes.find_one({'depute_age':{'$gt':80}}))
    pgroup = {}

    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'sexe':'$depute_sexe','age':'$depute_age','position':'$vote_position'}
    pipeline = [{'$group':pgroup}]
    grps = []
    pchart = {'Homme':[None]*20,'Femme':[None]*20}

    for agg in mdb.votes.aggregate(pipeline):
        a = agg['_id']
        if a['age']<20:
            print a

        classeage = int(a['age']/5)
        if not pchart[a['sexe']][classeage]:
            pchart[a['sexe']][classeage] = dict(pour=0,contre=0,absent=0,abstention=0)
        pchart[a['sexe']][classeage][a['position']] += agg['n']



    #return json_response(data)
    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;"
          )

    import datetime
    pyramid_chart = pygal.Pyramid(human_readable=True, x_title='% de participation',y_title="classes d'age",style=custom_style)
    pyramid_chart.title = u'Répartition de la participation aux scrutins publics\npar age et par sexe (au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    pyramid_chart.x_labels = ['%d-%d'% (a*5,(a+1)*5) for a in range(18)]

    for s in ['Femme','Homme']:
        items = []
        for ca in pchart[s]:
            if ca:
                items.append(round(100*float(ca['pour']+ca['contre']+ca['abstention'])/sum(ca.values()),0))
            else:
                items.append(0)
        pyramid_chart.add(s+'s',items)
    from StringIO import StringIO
    chart = StringIO()
    pyramid_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())
