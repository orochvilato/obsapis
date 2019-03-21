# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

from obsapis.config import cache_pages_delay

@app.route('/charts/groupes')
def propgroupes():
    pie_chart = pygal.Pie(half_pie=True)
    pie_chart.title = 'Browser usage in February 2012 (in %)'
    pie_chart.add('IE', 19.5)
    pie_chart.add('Firefox', 36.6)
    pie_chart.add('Chrome', 36.3)
    pie_chart.add('Safari', 4.5)
    pie_chart.add('Opera', 2.3)
    from StringIO import StringIO
    chart = StringIO()
    pie_chart.render_to_file(chart)
    return image_response('svg',chart.getvalue())




@app.route('/charts/compatdepute')
def chart_compatdep():
    deputes = request.args.get('depute','francoisruffin').split(',')

    dep_cpt = mdb.deputes.find({'depute_shortid':{'$in':deputes}},{'depute_nom':1,'stats.compat':1,'_id':None})
    radar_chart = pygal.Radar(fill=True,legend_at_bottom=True,height=650,width=600)
    groupes = ['FI','GDR','NG','LAREM','MODEM','UDI-AGIR','LR']
    radar_chart.title = u'Compatibilités vote (vote pour aux amendements)'
    radar_chart.x_labels = groupes
    for d in dep_cpt:
        print d
        radar_chart.add(d['depute_nom'], [d['stats']['compat'][g] for g in groupes])
    #radar_chart.add('Firefox', [7473, 8099, 11700, 2651, 6361, 1044, 3797, 9450])
    #radar_chart.add('Opera', [3472, 2933, 4203, 5229, 5810, 1828, 9013, 4669])
    #radar_chart.add('IE', [43, 41, 59, 79, 144, 136, 34, 102])
    from StringIO import StringIO
    chart = StringIO()
    radar_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())


@app.route('/charts/classements')
def classements():
    return json_response(mdb.votes.find_one())
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'mois':{'$concat':[{'$substr':['$scrutin_date',6,4]},'-',{'$substr':['$scrutin_date',3,2]}]},'dep':'$depute_shortid','position':'$vote_position'}
    pipeline = [{'$group':pgroup}]
    mois = {}

    for agg in mdb.votes.aggregate(pipeline):
        m = agg['_id']['mois']
        d = agg['_id']['dep']
        p = agg['_id']['position']
        n = agg['n']


        if not d in mois.keys():
            mois[d] = {}
        if not m in mois[d].keys():
            mois[d][m] = {'absent':0,'abstention':0,'pour':0,'contre':0,'total':0}

        mois[d][m][p] += n
        mois[d][m]['total'] += n

    return json_response(mois['charlottelecocq'])




@app.route('/charts/groupesstats/<stat>')
def groupesstat(stat):
    pardepute = 'pardepute' in request.args.keys()
    params = {'nbmots':{'legende':'Nombre de mots','titre':u'Nombre de mots prononcés en session','xaxis':u'Nombre de mots'},
              'nbitvs':{'legende':"Nombre d'interventions",'titre':u"Nombre d'interventions en session",'xaxis':u"Nombre d'interventions"}}
    libelles = {'FI':u'France Insoumise',
                'LAREM':u'République en Marche',
                'UDI-AGIR': u'UDI, Agir et Indépendants',
                'GDR':u'Gauche Démocratique et Républicaine',
                'NG':u'Nouvelle Gauche',
                'MODEM':u'Mouvement Démocrate',
                'LR':u'Les Républicains',
                'NI':u'Députés Non Inscrits'
                }
    #return json_response(mdb.votes.find_one())
    pgroup = {}
    pgroup['n'] = {'$sum':'$stats.%s' % stat}
    pgroup['_id'] = { 'groupe':'$groupe_abrev'}
    pipeline = [{'$group':pgroup}]
    grps = {}

    for a in mdb.deputes.aggregate(pipeline):
        g = a['_id']['groupe']
        n = a['n']
        if g=='LC':
            g='UDI-AGIR'
        if not g in grps:
            grps[g] = 0
        grps[g] += n



    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          title_font_size=18,
          value_font_size=11,
          colors=['#25a87e','#e23d21','#213558','#bbbbbb']
          )
    nbmembres = dict((g['groupe_abrev'],g['groupe_nbmembres']) for g in mdb.groupes.find({},{'groupe_nbmembres':1,'groupe_abrev':1,'_id':None}))
    stats = sorted(grps.items(),key=lambda x:x[1])
    pardep =u" par député" if pardepute else ""
    histo_chart = pygal.HorizontalBar(print_values=True,show_x_labels=False,show_legend=True,x_label_rotation=0,width=1024,height=512,human_readable=True,y_title="Groupes parlementaires",style=custom_style)
    histo_chart.title = params[stat]['titre']+pardep+u'\n par groupe parlementaire (au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    histo_chart.add( params[stat]['xaxis'], [stat[1] for stat in stats])
    histo_chart.add(u'nombre de députés', [nbmembres[stat[0]] for stat in stats])
    #histo_chart.add('par député', [stat[2] for stat in stats])

    histo_chart.x_labels = [libelles[stat[0]] for stat in stats]
    #histo_chart.x_labels_major = majors


    from StringIO import StringIO
    chart = StringIO()
    histo_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())


@app.route('/charts/groupesstats')
def groupesstats():

    params = {'nbmots':{'legende':'Nombre de mots','titre':u'Nombre de mots prononcés en session','xaxis':u'Nombre de mots'},
              'nbitvs':{'legende':"Nombre d'interventions",'titre':u"Nombre d'interventions en session",'xaxis':u"Nombre d'interventions"}}
    params = {'stats.nbmots':{'legende':'Nombre de mots'},
              'stats.nbitvs':{'legende':"Nombre d'interventions"},
              'groupe_nbmembres':{'legende':'Nombre de membres'}}
              #'stats.positions.exprimes':{'legende':'Participation aux\nscrutins publics'}}

    grporder = ('FI','LAREM','LR','MODEM','GDR','NG','UDI-AGIR','NI')
    libelles = {'FI':u'France Insoumise',
                'LAREM':u'République en Marche',
                'UDI-AGIR': u'UDI, Agir et Indépendants',
                'GDR':u'Gauche Démocratique et Républicaine',
                'NG':u'Nouvelle Gauche',
                'MODEM':u'Mouvement Démocrate',
                'LR':u'Les Républicains',
                'NI':u'Députés Non Inscrits'
                }
    groupes =  dict((g['groupe_abrev'],g) for g in mdb.groupes.find({'groupe_abrev':{'$ne':'LC'}},{'groupe_abrev':1,'groupe_nbmembres':1,'stats':1,'_id':None}))


    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          title_font_size=18,
          value_font_size=11,
          colors=['#25a87e','#e23d21','#213558','#bbbbbb']
          )

    maxs = {}
    stats = dict((item,[]) for item in params.keys())

    for item in params.keys():
        for g in reversed(grporder):
            stats[item].append(getdot(groupes[g],item))
        maxs[item]=max(stats[item])





    histo_chart = pygal.HorizontalBar(truncate_legend=-1,print_values=True,show_x_labels=False,show_legend=True,width=1024,height=512,human_readable=True,style=custom_style)
    histo_chart.title = "Statistiques des groupes parlementaires (au %s)" % (datetime.datetime.now().strftime('%d/%m/%Y'))

    def formatter(v):
        return lambda y:"%.0f" % (y*v)
    for item in params.keys():
        histo_chart.add( params[item]['legende'], [float(x)/maxs[item] for x in stats[item]], formatter=formatter(maxs[item]))

    #histo_chart.add('par député', [stat[2] for stat in stats])

    histo_chart.x_labels = [libelles[g] for g in reversed(grporder)]
    #histo_chart.x_labels_major = majors


    from StringIO import StringIO
    chart = StringIO()
    histo_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())


@app.route('/charts/comparestats/<elts>')
def comparestats(elts):
    elts = elts.split(',')
    items = {'vote':{'legende':'% de vote au scrutins publics','valeur':{'G':'stats.positions.exprimes','D':'stats.positions.exprimes'}},
             'commission':{'legende':u'% de présence en commission','valeur':{'G':'stats.commissions.toutes.present','D':'stats.commissions.present'}},
             'amendements':{'legende':u"Nombre d'amendements (par député)",'valeur':{'G':'stats.amendements.rediges','D':'stats.amendements.rediges'},'ponderation':True},
             'nbmots':{'legende':u'Nombre de mots (par député)','valeur':{'G':'stats.nbmots','D':'stats.nbmots'},'ponderation':True},
               'nbitvs':{'legende':u"Nombre d'interventions (par député)",'valeur':{'G':'stats.nbitvs','D':'stats.nbitvs'},'ponderation':True},
               }
    statorder = ['nbmots','nbitvs','amendements','commission','vote']
    depstats = dict((d['depute_shortid'],d) for d in mdb.deputes.find({'depute_shortid':{'$in':elts}},{'depute_nomcomplet':1,'depute_shortid':1,'stats':1,'_id':None}))
    gpstats = dict((g['groupe_abrev'],g) for g in mdb.groupes.find({'groupe_abrev':{'$in':elts}},{'groupe_abrev':1,'groupe_libelle':1,'stats':1,'groupe_nbmembres':1,'_id':None}))
    titres = {}
    valeurs = {}
    for e in elts:
        valeurs[e]=[]
        if e in depstats.keys():
            titres[e] = depstats[e]['depute_nomcomplet']
            nb = 1
            v = 'D'
            stats = depstats[e]
        elif e in gpstats.keys():
            titres[e] = gpstats[e]['groupe_libelle']

            nb = gpstats[e]['groupe_nbmembres']
            v = 'G'
            stats = gpstats[e]
        for it in statorder:
            itdef = items[it]
            pond = nb if itdef.get('ponderation',False) else 1
            valeurs[e].append(getdot(stats,itdef['valeur'][v])/pond)


    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          title_font_size=18,
          value_font_size=11,
          colors=['#25a87e','#e23d21','#213558','#bbbbbb']
          )

    maxs = {}
    for i,st in enumerate(statorder):
        maxs[st] = max([valeurs[e][i] for e in elts])
    #return json_response({'titres':titres,'valeurs':valeurs,'maxs':maxs})


    histo_chart = pygal.HorizontalBar(truncate_legend=-1,print_values=True,show_x_labels=False,show_legend=True,width=1024,height=512,human_readable=True,style=custom_style)
    histo_chart.title = u"Comparaison activité (au %s)" % (datetime.datetime.now().strftime('%d/%m/%Y'))

    def formatter(v):
        return lambda y:"%.0f" % (y*v)
    for elt in elts:
        histo_chart.add( titres[elt], [{'value':float(x)/maxs[statorder[i]],'formatter':formatter(maxs[statorder[i]])} for i,x in enumerate(valeurs[elt])])

    #histo_chart.add('par député', [stat[2] for stat in stats])

    histo_chart.x_labels = [items[item]['legende'] for item in statorder]
    #histo_chart.x_labels_major = majors


    from StringIO import StringIO
    chart = StringIO()
    histo_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())





@app.route('/charts/participationgroupes')
def votesgroupes():
    #return json_response(list(mdb.groupes.find({},{'_id':None,'groupe_abrev':1,'groupe_uid':1})))
    libelles = {'FI':u'France Insoumise',
                'LAREM':u'République en Marche',
                'UDI-AGIR': u'UDI, Agir et Indépendants',
                'GDR':u'Gauche Démocratique et Républicaine',
                'NG':u'Nouvelle Gauche',
                'MODEM':u'Mouvement Démocrate',
                'LR':u'Les Républicains',
                'NI':u'Députés Non Inscrits'
                }
    #return json_response(mdb.votes.find_one())
    pgroup = {}
    pgroup['n'] = {'$sum':1}
    pgroup['_id'] = { 'groupe':'$groupe_abrev','position':'$vote_position'}
    pipeline = [{'$group':pgroup}]
    grps = {}

    for v in mdb.votes.aggregate(pipeline):
        g = v['_id']['groupe']
        p = v['_id']['position']
        n = v['n']
        if g=='LC':
            g='UDI-AGIR'
        if not g in grps:
            grps[g] = { 'absent':0,'pour':0,'contre':0,'abstention':0 }
        grps[g][p] += n
    stats = []
    for g in grps:
        stat = dict(g=g)
        tot  = sum(grps[g].values())
        for p in ('pour','contre','abstention','absent'):
            stat[p]=100*float(grps[g][p])/tot

        stats.append(stat)
    stats.sort(key=lambda x:x['absent'],reverse=True)

    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          colors=['#25a87e','#e23d21','#213558','#bbbbbb']
          )


    histo_chart = pygal.HorizontalStackedBar(x_label_rotation=0,width=1024,height=512,human_readable=True, x_title='%',y_title="Groupes parlementaires",style=custom_style)
    histo_chart.title = u'Votes des députés aux scrutins publics\n par groupe parlementaire (au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    for x in 'pour','contre','abstention','absent':
        histo_chart.add('%s' % x, [stat[x] for stat in stats])
    histo_chart.x_labels = [libelles[stat['g']] for stat in stats]
    histo_chart.y_labels = []
    #histo_chart.x_labels_major = majors


    from StringIO import StringIO
    chart = StringIO()
    histo_chart.render_to_png(chart)
    return image_response('png',chart.getvalue())
    return json_response(stats)

@app.route('/charts/participationscrutins')
@cache_function(expires=cache_pages_delay)
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

@app.route('/charts/participation')
def charts_participation():
    print request.args_as_dict()
    buckets = [0]*10
    for d in mdb.deputes.find({'depute_actif':True},{'stats.positions.exprimes':1}):
        if 'positions' in d['stats'].keys():
            buckets[int(d['stats']['positions']['exprimes'])/10] += 1
    #return json_response(dict(n=sum(buckets),buckets=buckets))


    #return json_response(data)
    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;"
          )

    import datetime
    barchart = pygal.Bar(human_readable=True, show_legend=False,x_title=u'% de participation',y_title=u"nb de députés",style=custom_style)
    barchart.title = u'Participation aux scrutins publics\n(au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    barchart.x_labels = ["%d-%d" % (n*10,9+n*10) for n in range(10)]
    barchart.add('nb', buckets)

    from StringIO import StringIO
    chart = StringIO()
    barchart.render_to_png(chart)
    return image_response('png',chart.getvalue())
