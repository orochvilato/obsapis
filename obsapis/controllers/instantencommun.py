# -*- coding: utf-8 -*-
from obsapis import app,mdb
from obsapis.tools import json_response,image_response,getdot,maj1l,use_cache
import requests
from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image,ImageFont,ImageDraw
import StringIO
import datetime
import pygal
import re

def visueliec1():

    from pygal.style import Style
    custom_style = Style(
          font_family="'Montserrat', sans-serif;",
          major_label_font_size=15,
          title_font_size=18,
          value_font_size=11,
          opacity=1,
          background='transparent',
          plot_background='transparent',
          colors=['#25a87e','#e23d21','#213558','#bbbbbb']
          )

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/instantencommun'

    vis = Image.open(vispath+'/instantencommun.jpg')

    fontlegendb = ImageFont.truetype("Montserrat-SemiBold.ttf", 20)
    fontlegend  = ImageFont.truetype("Montserrat-Regular.ttf", 16)
    fontdos = ImageFont.truetype("Montserrat-Bold.ttf", fontdossize)
    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", fontnomsize)

    textes = Image.new('RGBA',(675,675))
    d = ImageDraw.Draw(textes)
    d.text((100,100), Test, font=fonttheme, fill=(255,255,255,255))


    vis.paste(textes,(0,0),textes)


    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
