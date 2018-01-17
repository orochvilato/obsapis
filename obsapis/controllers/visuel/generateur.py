# -*- coding: utf-8 -*-
from obsapis import app,mdb
from obsapis.tools import json_response,image_response,getdot,maj1l,use_cache
from flask import url_for
import requests
from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image,ImageChops,ImageFont,ImageDraw
from string import Template
import StringIO
import datetime
import pygal
import re
from io import BytesIO

def trim(im, border):
  bg = Image.new(im.mode, im.size, border)
  diff = ImageChops.difference(im, bg)
  bbox = diff.getbbox()
  if bbox:
    return im.crop(bbox)

from obsapis.controllers.emojis import get_emojis_css


def gentest():
    contenu = "Denique Antiochensis \n#ordinis vertices sub\n uno elogio iussit occidi ideo efferatus, quod ei celebrari vilitatem intempestivam urgenti, cum inpenderet inopia, gravius rationabili responderunt; et perissent ad unum ni comes orientis tunc Honoratus fixa constantia restitisset."

    im2 = txt_to_img(content=contenu,align='justify',padding=0,width=595,height=675,fontsize=32)

    texte_width,texte_height = im2.size
    final = im2
    output = StringIO.StringIO()
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()



def txt_to_img(content,width,height,align="left",padding=0,fontfamily="Roboto, sans-serif",fontsize=32,fontcolor='black',weightnormal=300,weightbold=500,bgcolor='#faf7ee'):
    html = Template("""<meta charset="UTF-8">
<html>
    <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">
    <style>
        body {
            background-color: ${bgcolor};
            font-family: ${fontfamily};
            font-size: ${fontsize}px;
            font-weight: ${weightnormal};
            color: ${fontcolor};
            padding: ${padding};
            margin:0;
            text-align: ${align};
        }
        strong,em {
            font-weight: ${weightbold};
        }
        strong {
            font-style: italic;
        }
        em {
            color: ${color}
        }
        italic {
            font-style: italic;
        }
        ${css}
    </style>
    </head>
    <body>${content}</body>
</html>""")
    import markdown
    import imgkit
    options = {
    'quiet': '',
    "xvfb": "",
    'format':'png',
    'width': width,
    'height': height,
     'encoding': "UTF-8",
    }
    emolist = []
    for i,e in enumerate(re.findall(r':[^:]+:',content)):
        emo = e[1:-1].split('|')
        size = fontsize
        color = None
        if len(emo)>1:
            for _e in emo[1:]:
                if _e[0]=='#':
                    color = _e
                else:
                    try:
                        size = int(_e)
                    except:
                        pass

        emolist.append((emo[0],size,color))

    _dec = re.split(r':[^:]+:',content)
    newcont = _dec[0]
    for i,txt in enumerate(_dec[1:]):
        if emolist[i][0][0:3]=='fa-':
            newcont += '<i class="fa %s item%d"></i>' % (emolist[i][0],i)
        elif ord(emolist[i][0][0])>255:
            path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets','emojis','svg'])
            code = []
            for c in emolist[i][0]:
                code.append(hex(int('0x'+repr(c)[4:-1],16))[2:])
            code = '-'.join(code)

            svg = open(path+'/%s.svg' % code).read()
            svg = re.sub(r'<\?[^?]+\?>','',svg)
            newcont += '<span class="emojisvg%d">%s</span>' % (i,svg)
        else:
            newcont += '<emoji class="e%s item%d"></emoji>' % (emolist[i][0],i)
        newcont += txt

    contenu = newcont
    contenu = re.sub(r'~([^~]+)~',r'<italic>\1</italic>',contenu)
    print markdown.markdown(contenu)
    htmlsource = html.substitute(bgcolor=bgcolor,css=get_emojis_css(emolist),
                                 weightnormal=weightnormal,weightbold=weightbold,
                                 fontcolor=fontcolor, align=align, padding=padding,color=fontcolor,
                                 content=markdown.markdown(contenu),fontfamily=fontfamily,fontsize=fontsize)


    img = imgkit.from_string(htmlsource,False,options=options)
    im = Image.open(BytesIO(img))
    return im
