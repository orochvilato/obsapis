# -*- coding: utf-8 -*-
from obsapis import app,mdb
from obsapis.tools import json_response,image_response,getdot,maj1l,use_cache
from flask import url_for
import requests
from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image,ImageChops,ImageFont,ImageDraw
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

def visueliec1(theme,themecustom,titre,couleur,contenu,source):
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/instantencommun'

    couleurs = { "violet": "#865e91",
"bleu": "#4575b5",
"vert": "#6bb592",
"jaune": "#edbd45",
"orange": "#fa9a46",
"rouge": "#cc4033" }


    html = """<meta charset="UTF-8">
<html>
    <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">
    <style>
        body {
            background-color: #faf7ee;
            font-family: Roboto, sans-serif;
            font-size: 32px;
            font-weight: 300;
        }
        strong,em {
            font-weight: 500;
        }
        strong {
            font-style: italic;
        }
        em {
            color: %s
        }
        italic {
            font-style: italic;
        }
        .test svg {
            width:40px;
            height:40px;
        }
        %s

    </style>
    </head>
    <body>%s</body>
</html>"""
    texte_width = 595
    import markdown
    import imgkit
    options = {
    'quiet': '',
    "xvfb": "",
    'format':'png',
    'width': texte_width,
    'height': 675,
     'encoding': "UTF-8",
    }
    emolist = []
    for i,e in enumerate(re.findall(r':[^:]+:',contenu)):
        emo = e[1:-1].split('|')
        size = 32
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

    _dec = re.split(r':[^:]+:',contenu)
    newcont = _dec[0]
    for i,txt in enumerate(_dec[1:]):
        if emolist[i][0][0:3]=='fa-':
            newcont += '<i class="fa %s item%d"></i>' % (emolist[i][0],i)
        elif ord(emolist[i][0][0])>255:
            path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets','emojis','svg'])
            code = hex(int('0x'+repr(emolist[i][0])[4:-1],16))[2:]

            svg = open(path+'/%s.svg' % code).read()
            svg = re.sub(r'<\?[^?]+\?>','',svg)
            newcont += '<span class="emojisvg%d">%s</span>' % (i,svg)

        else:
            newcont += '<emoji class="e%s item%d"></emoji>' % (emolist[i][0],i)
        newcont += txt

    contenu = newcont
    contenu = re.sub(r'~([^~]+)~',r'<italic>\1</italic>',contenu)

    htmlsource = html % (couleurs[couleur],get_emojis_css(emolist),markdown.markdown(contenu))
    

    img = imgkit.from_string(htmlsource,False,options=options)
    im = Image.open(BytesIO(img))

    im2 = trim(im,(250,247,238))
    texte_width,texte_height = im2.size


    output = StringIO.StringIO()

    vis = Image.open(vispath+'/iec_%s.png' % couleur)

    titre = themecustom if themecustom else titre
    titre = titre.upper()



    textes = Image.new('RGBA',(675,675))
    d = ImageDraw.Draw(textes)
    reduce = 0
    theme_w = 100000
    while theme_w>370:
        themefont = ImageFont.truetype("Montserrat-ExtraBold.ttf", 28-reduce)
        theme_w,theme_h = themefont.getsize(titre)
        reduce += 1

    d.text((10+(370-theme_w)/2,122+reduce/2), titre, font=themefont, fill=(255,255,255,255))


    textes = textes.rotate(2.8,expand=1,resample=Image.BICUBIC)

    sourcefont = ImageFont.truetype("Montserrat-LightItalic.ttf",14)
    sources =Image.new('RGBA',(675,675))
    s = ImageDraw.Draw(sources)

    s.text((((675-texte_width)/2),425+texte_height/2), 'Source : '+source, font=sourcefont, fill=(0,0,0,255))
    vis.paste(im2,(((675-texte_width)/2),175+(450-texte_height)/2),im2)
    vis.paste(textes,(0,0),textes)
    vis.paste(sources,(0,0),sources)

    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
