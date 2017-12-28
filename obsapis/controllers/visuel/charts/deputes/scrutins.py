# -*- coding: utf-8 -*-

from obsapis import app,use_cache,mdb
from flask import request
from obsapis.tools import image_response,json_response,cache_function, getdot, strip_accents, logitem
import re
import random
import datetime
import pygal

def participation_globale_par_tranche_de_10(width=800,height=600,background="#ffffff"):
    buckets = [0]*10
    for d in mdb.deputes.find({'depute_actif':True},{'stats.positions.exprimes':1}):
        if 'positions' in d['stats'].keys():
            buckets[int(d['stats']['positions']['exprimes'])/10] += 1
    #return json_response(dict(n=sum(buckets),buckets=buckets))


    #return json_response(data)
    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          background=background,
          plot_background='transparent',
          title_font_size=16,
          colors = ('#ff0052','#ff0052')

          )

    import datetime
    barchart = pygal.Bar(human_readable=True, width=width,height=height,show_legend=False,x_title=u'% de participation',y_title=u"nombre\nde députés",style=custom_style)
    barchart.title = u'Participation aux scrutins publics (au %s)' % (datetime.datetime.now().strftime('%d/%m/%Y'))
    barchart.x_labels = ["%d-%d" % (n*10,9+n*10) for n in range(10)]
    barchart.add('nb', buckets)



    from StringIO import StringIO
    chart = StringIO()
    barchart.render_to_png(chart)
    return chart.getvalue()
