# -*- coding: utf-8 -*-
from obsapis import app,mdb
from obsapis.tools import json_response,image_response,getdot,maj1l,use_cache

from PIL import Image,ImageFont,ImageDraw
import StringIO
import datetime
import pygal
import re

def visuelmacaron(elements=[]):
    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21'
    vis = Image.open(vispath+'/share_2-1_fond.png')
    poster = Image.open(vispath+'/share_2-1_poster.png')
    plis = Image.open(vispath+'/share_2-1_plis.png')
    footer = Image.open(vispath+'/share_2-1_footer.png')

    vis.paste(poster,(0,0),poster)
    for e in elements:
        imstr,x,y = e
        f_im = StringIO.StringIO(imstr)
        im = Image.open(f_im)
        vis.paste(im,(x,y))



    vis.paste(plis,(0,0),plis)
    vis.paste(footer,(0,0),footer)
    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()

def visuelclean(elements=[]):

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21clean'

    vis = Image.open(vispath+'/share_obs_clean.png')
    for e in elements:
        imstr,x,y = e
        f_im = StringIO.StringIO(imstr)
        im = Image.open(f_im)
        vis.paste(im,(x,y))

    #Custom
    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
