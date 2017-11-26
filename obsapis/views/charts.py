# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

@app.route('/charts/participationscrutins')
def participationscrutins():
    data = {'pour':[],'contre':[],'abstention':[],'absent':[]}
    xlabels = []
    majors = []
    i=0
    scrutins = list(mdb.scrutins.find({},{'scrutin_date':1,'scrutin_num':1,'scrutin_positions.assemblee':1,'_id':None}))
    for s in scrutins:
        for x in 'pour','contre','abstention','absent':
            v = 100*float(s['scrutin_positions']['assemblee'].get(x,0))/s['scrutin_positions']['assemblee']['total']
            data[x].append(v)


            lab = "%d" % (s['scrutin_num'])
            xlabels.append(lab)
            majors.append(lab)
        else:
            xlabels.append("")
        i += 1



    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          colors=['#25a87e','#e23d21','#213558','#dddddd']
          )


    histo_chart = pygal.StackedBar(x_label_rotation=90,width=1024,height=512,human_readable=True, x_title='Scrutins',y_title="%",style=custom_style)
    histo_chart.title = u'Positions lors des scrutins\n (au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    for x in 'pour','contre','abstention','absent':
        histo_chart.add('%s' % x, data[x])
    #histo_chart.x_labels = xlabels
    #histo_chart.x_labels_major = majors


    from StringIO import StringIO
    chart = StringIO()
    histo_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())


@app.route('/charts/pyramideage')
def pyramideage():
    return json_response(mdb.scrutins.find_one())
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



@app.route('/charts/pyramidepartipation')
def pyramideparticipation():
    return json_response(mdb.scrutins.find_one())
    pgroup = {}

    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'sexe':'$depute_sexe','position':'$vote_position'}
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
