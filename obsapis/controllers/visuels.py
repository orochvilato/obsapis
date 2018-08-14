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

from obsapis.controllers.scrutins import getScrutinsCles
from obsapis.controllers.scrutins import getScrutinsPositions

params = {'participation':{'type':'gauge','field':'stats.positions.exprimes','label':['Participation aux','scrutins publics']},
          'commission':{'type':'gauge','field':'stats.commissions.present','label':['Présence en','commission']},
          'absent':{'type':'gauge','field':'stats.positions.absent','label':['Absence lors des','scrutins publics']},
          'motspreferes':{'type':'texte','field':'depute_nuages','label':['Ses mots','préférés']},
          'verbespreferes':{'type':'texte','field':'depute_nuages','label':['Ses verbes','préférés']},
          }

def maxis():
    maxcirco = []
    maxnom = []
    maxgp = []
    maxmot = []
    for dep in mdb.deputes.find({},{'depute_nuages':1,'depute_shortid':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}):
        id = dep['depute_shortid']
        if dep['depute_region']==dep['depute_departement']:
            circo =  "%s (999) / %se circ" % (dep['depute_departement'],dep['depute_circo'])
        else:
            circo =  "%s / %s (999) / %se circ" % (dep['depute_region'],dep['depute_departement'],dep['depute_circo'])
        maxcirco.append((id,len(circo)))
        maxnom.append((id,len(dep['depute_nom'])))
        if dep['depute_nuages']:
            maxmot.append(dep['depute_nuages']['noms'][0][0])
        gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])
        maxgp.append((id,len(gp)))
        maxcirco.sort(key=lambda x:x[1],reverse=True)
        maxnom.sort(key=lambda x:x[1],reverse=True)
        maxgp.sort(key=lambda x:x[1],reverse=True)
        maxmot.sort(reverse=True)
    return dict(circo=maxcirco[:10],nom=maxnom[:10],gp=maxgp[:10],mot=maxmot[:10])

def genvisuelstat(depute,stat):

    stats = stat.split(',')
    fields = {'depute_photo':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_departement_id':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}
    fields.update(dict((p['field'],1) for p in params.values()))
    dep = mdb.deputes.find_one({'depute_shortid':depute},fields)

    if not dep:
        return "nope"
    numdep = dep['depute_departement_id'][1:] if dep['depute_departement_id'][0]=='0' else dep['depute_departement_id']
    if dep['depute_region']==dep['depute_departement']:
        circo =  "%s (%s) / %se circ" % (dep['depute_departement'],numdep,dep['depute_circo'])
    else:
        circo =  "%s / %s (%s) / %se circ" % (dep['depute_region'],dep['depute_departement'],numdep,dep['depute_circo'])
    gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])


    from base64 import b64decode

    photo = StringIO.StringIO(b64decode(dep['depute_photo']))
    photo = Image.open(photo)
    photo = photo.resize((int(1.4*photo.size[0]),int(1.4*photo.size[1])))

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat'

    vis = Image.open(vispath+'/obs_share_square_fond.png')
    poster = Image.open(vispath+'/obs_share_square_poster.png')
    plis = Image.open(vispath+'/obs_share_square_plis.png')
    footer = Image.open(vispath+'/obs_share_square_footer_eyeopen.png')

    # make a blank image for the text, initialized to transparent text color
    textes = Image.new('RGBA',(1024,1024))
    # get a drawing context
    d = ImageDraw.Draw(textes)
    # draw text, half opacity

    h = 38
    fontcirco = ImageFont.truetype("Montserrat-Bold.ttf", 19)
    circ_w,circ_h = fontcirco.getsize(circo)
    circ_pad = (h - circ_h)/2
    circ_x,circ_y = 12+photo.size[1],100
    d.rectangle(((circ_x, circ_y), (circ_x+circ_w+2*6, circ_y+circ_h+2*circ_pad)), fill=(255,0,82,255))
    d.text((circ_x+6,circ_y+circ_pad), circo, font=fontcirco, fill=(255,255,255,255))

    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", 30)
    nom_w,nom_h = fontnom.getsize(dep['depute_nom'])
    nom_pad = (h- nom_h)/2
    nom_x,nom_y = circ_x,circ_y+h
    d.rectangle(((nom_x, nom_y), (nom_x+nom_w+2*6, nom_y+nom_h+2*nom_pad)), fill=(33,53,88,255))
    d.text((nom_x+6,nom_y+nom_pad-3), dep['depute_nom'], font=fontnom, fill=(255,255,255,255))
    fontgen = ImageFont.truetype("Montserrat-Regular.ttf", 11)
    dategen = 'Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')
    d.text((840,570),dategen.decode('utf8'),font=fontgen,fill=(10,10,10,255))
    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 34)
    vis.paste(poster,(0,0),poster)
    vis.paste(photo,(70,139))

    if len(stats)==1 and params[stat]['type']=='gauge':
        statimage = Image.open(path+'/assets/%s/%d.png' % (stat,round(getdot(dep,params[stat]['field']),0))).resize((300,300),Image.ANTIALIAS)
        vis.paste(statimage,(340,220))
        for i,l in enumerate(params[stat]['label']):
            d.text((660,282+i*45),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))
    elif stat=='motspreferes':
        fontmot1 = ImageFont.truetype("Montserrat-Bold.ttf", 55)
        fontmot = ImageFont.truetype("Montserrat-Bold.ttf", 35)

        if dep['depute_nuages']:
            # 320
            mots = [x[0] for x in dep['depute_nuages']['noms'][:5]]
            d.text((360,200),"1. "+maj1l(mots[0]),font=fontmot1,fill=(255,0,82,255))
            for i in range(1,5):
                d.text((360,270+(i-1)*45),"%d. %s" % (1+i,maj1l(mots[i])),font=fontmot,fill=(33,53,88,255))

            d.text((400,485),"Ses mots préférés".decode('utf8'), font=fontlabel,fill=(130,205,226,255))
    elif len(stats)==2:
        fontmot1 = ImageFont.truetype("Montserrat-Bold.ttf", 36)
        fontmot = ImageFont.truetype("Montserrat-Bold.ttf", 25)
        fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 28)
        for j,stat in enumerate(stats):
            label = True
            if stat in params.keys():
                if params[stat]['type']=='gauge':
                    statimage = Image.open(path+'/assets/%s/%d.png' % (stat,round(getdot(dep,params[stat]['field']),0))).resize((250,250),Image.ANTIALIAS)
                    vis.paste(statimage,(350+315*j,200))
                elif stat=='motspreferes':
                    if dep['depute_nuages']:
                        mots = [x[0] for x in dep['depute_nuages']['noms'][:5]]
                        d.text((350+315*j,220),"1. "+maj1l(mots[0]),font=fontmot1,fill=(255,0,82,255))
                        for i in range(1,5):
                            d.text((350+315*j,270+(i-1)*40),"%d. %s" % (1+i,maj1l(mots[i])),font=fontmot,fill=(33,53,88,255))
                        d.text((350+315*j,462),"Ses mots préférés".decode('utf8'), font=fontlabel,fill=(130,205,226,255)) #462
                        label = False

                if label:
                    for i,l in enumerate(params[stat]['label']):
                        w,h = fontlabel.getsize(l.decode('utf8'))
                        d.text((350+315*j+(250-w)/2,445+i*34),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))

    vis.paste(textes,(0,0),textes)

    vis.paste(plis,(0,0),plis)
    vis.paste(footer,(0,0),footer)
    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()


def genvisuelstat21(depute,stat):
    stats = stat.split(',')
    fields = {'depute_photo':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement_id':1,'depute_departement':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}
    fields.update(dict((p['field'],1) for p in params.values()))
    dep = mdb.deputes.find_one({'depute_shortid':depute},fields)

    if not dep:
        return "nope"

    numdep = dep['depute_departement_id'][1:] if dep['depute_departement_id'][0]=='0' else dep['depute_departement_id']
    if dep['depute_region']==dep['depute_departement']:
        circo =  "%s (%s) / %se circ" % (dep['depute_departement'],numdep,dep['depute_circo'])
    else:
        circo =  "%s / %s (%s) / %se circ" % (dep['depute_region'],dep['depute_departement'],numdep,dep['depute_circo'])

    gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])


    from base64 import b64decode

    photo = StringIO.StringIO(b64decode(dep['depute_photo']))
    photo = Image.open(photo)
    photo = photo.resize((int(1.0*photo.size[0]),int(1.0*photo.size[1])))

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21'

    vis = Image.open(vispath+'/share_2-1_fond.png')
    poster = Image.open(vispath+'/share_2-1_poster.png')
    plis = Image.open(vispath+'/share_2-1_plis.png')
    footer = Image.open(vispath+'/share_2-1_footer.png')

    # make a blank image for the text, initialized to transparent text color
    textes = Image.new('RGBA',(1024,1024))
    # get a drawing context
    d = ImageDraw.Draw(textes)
    # draw text, half opacity

    h = 30
    fontcirco = ImageFont.truetype("Montserrat-Bold.ttf", 14)
    circ_w,circ_h = fontcirco.getsize(circo)
    circ_pad = (h - circ_h)/2
    circ_x,circ_y = 272+photo.size[1],70
    d.rectangle(((circ_x, circ_y), (circ_x+circ_w+2*6, circ_y+circ_h+2*circ_pad)), fill=(255,0,82,255))
    d.text((circ_x+6,circ_y+circ_pad), circo, font=fontcirco, fill=(255,255,255,255))

    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", 22)
    nom_w,nom_h = fontnom.getsize(dep['depute_nom'])
    nom_pad = (h- nom_h)/2
    nom_x,nom_y = circ_x,circ_y+h
    d.rectangle(((nom_x, nom_y), (nom_x+nom_w+2*6, nom_y+nom_h+2*nom_pad)), fill=(33,53,88,255))
    d.text((nom_x+6,nom_y+nom_pad-1), dep['depute_nom'], font=fontnom, fill=(255,255,255,255))
    fontgen = ImageFont.truetype("Montserrat-Regular.ttf", 11)
    dategen = 'Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')
    d.text((840,367),dategen.decode('utf8'),font=fontgen,fill=(50,50,50,255))
    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 34)
    vis.paste(poster,(0,0),poster)
    vis.paste(photo,(314,100))



    statunique = (len(stats)==1)
    params_stats = {'gauge':{True:{'x':530,'y':150,'w':200},
                             False:{'x':510,'y':150,'w':140}
                            },
                    'label':{True:{'x':750,'y':210,'fs':22},
                             False:{'x':510,'y':295,'fs':18}
                             },
                    'mots':{True:{'x':510,'y':155,'space':45,'h':30,'xl':510,'yl':307,'fsmot1':30,'fsmot':22,'fslabel':20},
                            False:{'x':510,'y':150,'space':40,'h':25,'xl':510,'yl':307,'fsmot1':27,'fsmot':20,'fslabel':18}}
                   }
    for j,stat in enumerate(stats):
        label = True
        if stat in params.keys():
            if params[stat]['type']=='gauge':
                _ps = params_stats['gauge'][statunique]
                statimage = Image.open(path+'/assets/%s/%d.png' % (stat,round(getdot(dep,params[stat]['field']),0))).resize((_ps['w'],_ps['w']),Image.ANTIALIAS)
                vis.paste(statimage,(_ps['x']+220*j,_ps['y']))
            elif stat=='motspreferes' or stat=='verbespreferes':
                if dep['depute_nuages']:
                    _ps = params_stats['mots'][statunique]
                    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fslabel'])
                    fontmot1 = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fsmot1'])
                    fontmot = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fsmot'])

                    typemot = 'noms' if stat=='motspreferes' else 'verbes'
                    libelle = "Ses mots préférés".decode('utf8') if stat=='motspreferes' else "Ses verbes préférés".decode('utf8')
                    mots = [x[0] for x in dep['depute_nuages'][typemot][:5]]
                    d.text((_ps['x']+220*j,_ps['y']),"1. "+maj1l(mots[0]),font=fontmot1,fill=(255,0,82,255))
                    for i in range(1,5):
                        d.text((_ps['x']+220*j,_ps['y']+_ps['space']+(i-1)*_ps['h']),"%d. %s" % (1+i,maj1l(mots[i])),font=fontmot,fill=(33,53,88,255))
                    if not statunique:
                        d.text((_ps['xl']+220*j,_ps['yl']),libelle, font=fontlabel,fill=(130,205,226,255)) #462

                    label = statunique
                else:
                    _ps = params_stats['label'][statunique]
                    fontlabel = ImageFont.truetype("Montserrat-Regular.ttf", _ps['fs'])
                    corx,cory = (-200,0) if statunique else (0,-100)

                    for i,l in enumerate(['Aucune','intervention']):
                        w,h = fontlabel.getsize(l.decode('utf8'))
                        d.text((corx+_ps['x']+220*j+((150-w)/2)*(0 if statunique else 1),cory+_ps['y']+i*24),l.decode('utf8'), font=fontlabel,fill=(255,0,82,255))

            if label:
                _ps = params_stats['label'][statunique]
                fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fs'])
                for i,l in enumerate(params[stat]['label']):
                    w,h = fontlabel.getsize(l.decode('utf8'))
                    d.text((_ps['x']+220*j+((150-w)/2)*(0 if statunique else 1),_ps['y']+i*24),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))

    vis.paste(textes,(0,0),textes)

    vis.paste(plis,(0,0),plis)
    vis.paste(footer,(0,0),footer)
    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()

def genvisuelstat21clean(depute,stat):
    stats = stat.split(',')
    fields = {'depute_photo':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_departement_id':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}
    fields.update(dict((p['field'],1) for p in params.values()))
    dep = mdb.deputes.find_one({'depute_shortid':depute},fields)

    if not dep:
        return "nope"

    numdep = dep['depute_departement_id'][1:] if dep['depute_departement_id'][0]=='0' else dep['depute_departement_id']
    if dep['depute_region']==dep['depute_departement']:
        circo =  "%s (%s) / %se circ" % (dep['depute_departement'],numdep,dep['depute_circo'])
    else:
        circo =  "%s / %s (%s) / %se circ" % (dep['depute_region'],dep['depute_departement'],numdep,dep['depute_circo'])

    gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])


    from base64 import b64decode

    photo = StringIO.StringIO(b64decode(dep['depute_photo']))
    photo = Image.open(photo)
    photo = photo.resize((int(1.3*photo.size[0]),int(1.3*photo.size[1])))

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21clean'

    vis = Image.open(vispath+'/share_obs_clean.png')

    # make a blank image for the text, initialized to transparent text color
    textes = Image.new('RGBA',(1024,1024))
    # get a drawing context
    d = ImageDraw.Draw(textes)
    # draw text, half opacity

    h = 40
    fontcirco = ImageFont.truetype("Montserrat-Bold.ttf", 16)
    circ_w,circ_h = fontcirco.getsize(circo)
    circ_pad = (h - circ_h)/2
    circ_x,circ_y = -5+photo.size[1],20
    d.rectangle(((circ_x, circ_y), (circ_x+circ_w+2*6, circ_y+circ_h+2*circ_pad)), fill=(255,0,82,255))
    d.text((circ_x+6,circ_y+circ_pad), circo, font=fontcirco, fill=(255,255,255,255))

    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", 24)
    nom_w,nom_h = fontnom.getsize(dep['depute_nom'])
    nom_pad = (h- nom_h)/2
    nom_x,nom_y = circ_x,circ_y+h
    d.rectangle(((nom_x, nom_y), (nom_x+nom_w+2*6, nom_y+nom_h+2*nom_pad)), fill=(33,53,88,255))
    d.text((nom_x+6,nom_y+nom_pad-1), dep['depute_nom'], font=fontnom, fill=(255,255,255,255))
    fontgen = ImageFont.truetype("Montserrat-Regular.ttf", 13)
    dategen = 'Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')
    d.text((830,476),dategen.decode('utf8'),font=fontgen,fill=(255,255,255,255))
    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 34)

    vis.paste(photo,(50,60))


    fontmot1 = ImageFont.truetype("Montserrat-Bold.ttf", 34)
    fontmot = ImageFont.truetype("Montserrat-Bold.ttf", 28)
    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 22)


    statunique = (len(stats)==1)
    params_stats = {'gauge':{True:{'x':310,'y':135,'w':290},
                             False:{'x':310,'y':135,'w':250}
                            },
                    'label':{True:{'x':665,'y':220,'fs':32},
                             False:{'x':310,'y':380,'fs':22}
                             },
                    'mots':{True:{'x':310,'y':135,'space':65,'h':46,'xl':350,'yl':372,'fsmot1':38,'fsmot':32,'fslabel':28},
                            False:{'x':310,'y':135,'space':55,'h':42,'xl':310,'yl':392,'fsmot1':34,'fsmot':28,'fslabel':22}}
                   }

    if 0: #for j,stat in enumerate(stats):
        label = True
        if stat in params.keys():
            if params[stat]['type']=='gauge':
                statimage = Image.open(path+'/assets/%s/%d.png' % (stat,round(getdot(dep,params[stat]['field']),0))).resize((250,250),Image.ANTIALIAS)
                vis.paste(statimage,(310+330*j,135))
            elif stat=='motspreferes' or stat=='verbespreferes':
                print dep['depute_nuages']
                if dep['depute_nuages']:
                    typemot = 'noms' if stat=='motspreferes' else 'verbes'
                    libelle = "Ses mots préférés".decode('utf8') if stat=='motspreferes' else "Ses verbes préférés".decode('utf8')
                    mots = [x[0] for x in dep['depute_nuages'][typemot][:5]]
                    d.text((310+330*j,135),"1. "+maj1l(mots[0]),font=fontmot1,fill=(255,0,82,255))
                    for i in range(1,5):
                        d.text((310+330*j,190+(i-1)*42),"%d. %s" % (1+i,maj1l(mots[i])),font=fontmot,fill=(33,53,88,255))

                    d.text((310+330*j,392),libelle, font=fontlabel,fill=(130,205,226,255)) #462
                    label = False

            if label:
                for i,l in enumerate(params[stat]['label']):
                    w,h = fontlabel.getsize(l.decode('utf8'))
                    d.text((310+330*j+(250-w)/2,380+i*28),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))

    for j,stat in enumerate(stats):
        label = True
        if stat in params.keys():
            if params[stat]['type']=='gauge':
                _ps = params_stats['gauge'][statunique]
                statimage = Image.open(path+'/assets/%s/%d.png' % (stat,round(getdot(dep,params[stat]['field']),0))).resize((_ps['w'],_ps['w']),Image.ANTIALIAS)
                vis.paste(statimage,(_ps['x']+330*j,_ps['y']))
            elif stat=='motspreferes' or stat=='verbespreferes':

                if dep['depute_nuages']:
                    _ps = params_stats['mots'][statunique]
                    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fslabel'])
                    fontmot1 = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fsmot1'])
                    fontmot = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fsmot'])

                    typemot = 'noms' if stat=='motspreferes' else 'verbes'
                    libelle = "Ses mots préférés".decode('utf8') if stat=='motspreferes' else "Ses verbes préférés".decode('utf8')
                    mots = [x[0] for x in dep['depute_nuages'][typemot][:5]]
                    d.text((_ps['x']+330*j,_ps['y']),"1. "+maj1l(mots[0]),font=fontmot1,fill=(255,0,82,255))
                    for i in range(1,len(mots)):
                        d.text((_ps['x']+330*j,_ps['y']+_ps['space']+(i-1)*_ps['h']),"%d. %s" % (1+i,maj1l(mots[i])),font=fontmot,fill=(33,53,88,255))
                    if not statunique:
                        d.text((_ps['xl']+330*j,_ps['yl']),libelle, font=fontlabel,fill=(130,205,226,255)) #462

                    label = statunique
                else:
                    _ps = params_stats['label'][statunique]
                    fontlabel = ImageFont.truetype("Montserrat-Regular.ttf", _ps['fs'])
                    corx,cory = (-280,0) if statunique else (0,-180)

                    for i,l in enumerate(['Aucune','intervention']):
                        w,h = fontlabel.getsize(l.decode('utf8'))
                        d.text((corx+_ps['x']+330*j+((250-w)/2)*(0 if statunique else 1),cory+_ps['y']+i*(_ps['fs']+6)),l.decode('utf8'), font=fontlabel,fill=(255,0,82,255))

            if label:
                _ps = params_stats['label'][statunique]
                fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", _ps['fs'])
                for i,l in enumerate(params[stat]['label']):
                    w,h = fontlabel.getsize(l.decode('utf8'))
                    d.text((_ps['x']+330*j+((250-w)/2)*(0 if statunique else 1),_ps['y']+i*(_ps['fs']+6)),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))


    vis.paste(textes,(0,0),textes)

    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()







def getgauge():
    import os.path
    import time
    import os
    import StringIO

    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets'])
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    zone = (50,40,450,440)
    size = '500x600'
    options.add_argument('window-size=%s' % size)
    cdservice = service.Service('/usr/bin/chromedriver')
    cdservice.start()
    driver = webdriver.Chrome(chrome_options=options)

    for id in ['participation','commission','absent']:
        for pct in range(0,101):
            imgpath = path+'/%s/%d.png' %(id,pct)
            if os.path.isfile(imgpath):
                continue
            url = "http://dev.observatoire-democratie.fr/oropage/%s/%d" % (id,pct)
            open(imgpath,'w').write("0")
            driver.get(url)
            time.sleep(1)

            image = Image.open(StringIO.StringIO(driver.get_screenshot_as_png()))
            image = image.crop(zone)
            #output = StringIO.StringIO()
            #image.save(output,'PNG')
            image.save(imgpath,'PNG')
    driver.quit()
    cdservice.stop()
    return "ok"

def get_visuel(id,depute,regen=None,neutre=None):
    dep = mdb.deputes.find_one({'depute_shortid':depute},{'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None})
    if not dep:
        return "nope"
    if dep['depute_region']==dep['depute_departement']:
        circo =  "%s (999) / %se circ" % (dep['depute_departement'],dep['depute_circo'])
    else:
        circo =  "%s / %s (999) / %se circ" % (dep['depute_region'],dep['depute_departement'],dep['depute_circo'])
    gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])
    font1 = ImageFont.truetype("Montserrat-Bold.ttf", 14)
    font2 = ImageFont.truetype("Montserrat-Bold.ttf", 21)
    font3 = ImageFont.truetype("Montserrat-Bold.ttf", 11)

    wf1 = font1.getsize(circo)[0]/float(510)
    wf2 = font2.getsize(dep['depute_nom'])[0]/float(413)
    wf3 = font3.getsize(dep['depute_naissance'])[0]/float(457)
    wf4 = font3.getsize(gp)[0]/float(320)
    widthcor = 680*max(0.83,wf1,wf2,wf3,wf4)

    #widthcor = 565
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels',id])
    imgpath = path+'/tous/'+depute+'.png'
    import os.path
    if os.path.isfile(imgpath) and not regen:
        return open(imgpath).read()
    else:
        open(imgpath,'w').write("0")
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    if id=='obs1':
        factor = 1.2
        url = "http://dev.observatoire-democratie.fr/assemblee/deputes/recherche?requete=%s" % dep['depute_nom']
        zone = (120,560,860,804)
        size = '1000x1000'

    else:
        factor = 1.2
        url = "http://dev.observatoire-democratie.fr/assemblee/deputes/%s/votes" % depute
        zone = (90,310,840-(680-widthcor),570)
        size = '1200x1000'
    options.add_argument('window-size=%s' % size)
    options.add_argument('force-device-scale-factor=%0.1f' % factor)


    cdservice = service.Service('/usr/bin/chromedriver')
    cdservice.start()
    driver = webdriver.Chrome(chrome_options=options)
    #driver = webdriver.PhantomJS() # or add to your PATH
    #driver.set_window_size(1600, 1024) # optional
    driver.get(url)

    import os



    image = Image.open(StringIO.StringIO(driver.get_screenshot_as_png()))
    image2 = image.crop((factor*zone[0],factor*zone[1],factor*zone[2],factor*zone[3]))
    output = StringIO.StringIO()

    if id=="obs1":
        image3 = image2
        vis = Image.open(path+'/fiche_fond.png').resize((1024,1024))
        poster = Image.open(path+'/fiche_poster.png').resize((1024,1024))
        plis = Image.open(path+'/fiche_plis.png').resize((1024,1024))
        if neutre:
            footer = Image.open(path+'/fiche_macaron_footer_neutre.png').resize((1024,1024))
        else:
            footer = Image.open(path+'/fiche_macaron_footer.png').resize((1024,1024))

        vis.paste(poster,(0,0),poster)
        vis.paste(image3,(70,170))
        vis.paste(plis,(0,0),plis)
        vis.paste(footer,(0,0),footer)
        if neutre:
            final = vis.crop((0,0,1024,816))
        else:
            final = vis
    else:
        width, height = image2.size
        image3 = image2.resize((680,int(680*float(height)/width)),Image.ANTIALIAS) #680
        #image3 = image2
        vis = Image.open(path+'/share_2_1_fond.png') #.resize((1024,512))
        poster = Image.open(path+'/share_2_1_poster.png') #.resize((1024,512))
        plis = Image.open(path+'/share_2_1_plis.png') #.resize((1024,512))
        footer = Image.open(path+'/share_2_1_footer2.png') #.resize((1024,512))
        vis.paste(poster,(0,0),poster)
        vis.paste(image3,(300,80))
        vis.paste(plis,(0,0),plis)
        vis.paste(footer,(0,0),footer)
        final = vis

    #final = vis.resize((1024,1024))
    final.save(output,'PNG')
    final.save(imgpath,'PNG')
    driver.quit()
    return output.getvalue()


def visuelvotecle(num,groupe=None,fs=16,fst=20):
    groupeslibs = dict((g['groupe_abrev'],g['groupe_libelle']) for g in mdb.groupes.find({},{'groupe_abrev':1,'groupe_libelle':1}))
    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=3600)
    scrutins_positions = use_cache('scrutins_positions',lambda:getScrutinsPositions(),expires=36000)
    scrutin = mdb.scrutins.find_one({'scrutin_num':num})
    if not scrutin or not num in scrutins_cles:
        return ""
    scrutin.update(scrutins_cles[num])
    if scrutin['scrutin_dossierLibelle']!='N/A':
        scrutin['dossier'] = scrutin['scrutin_dossierLibelle']
    scrutin['dossier'] = scrutin['dossier'].replace(u'\u0092',"'")

    positions = scrutin['scrutin_positions'][groupe if groupe else 'assemblee']
    if scrutin['inversion'] == 'oui':
        positions['position'] = {'pour':'contre','contre':'pour'}.get(positions['position'],positions['position'])
        positions['pour'] = scrutins_positions[scrutin['scrutin_num']]['contre']
        positions['contre'] = scrutins_positions[scrutin['scrutin_num']]['pour']
    #return json_response(positions)
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
    pie_chart = pygal.Pie(inner_radius=.5,style=custom_style,show_legend=False,margin=0,width=512,height=440)
    for pos in ('pour','contre','abstention','absent'):
        pie_chart.add("%d %s" % (positions.get(pos,0),pos), positions.get(pos,0))


    chart = StringIO.StringIO()
    pie_chart.render_to_png(chart)

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21clean'

    vis = Image.open(vispath+'/share_obs_clean.png')
    imchart = Image.open(chart)

    cropcircle = Image.new('RGBA',(400,400))
    cc = ImageDraw.Draw(cropcircle)
    cc.ellipse((0, 0, 400, 400), fill = 'white')
    ccircle = cropcircle.resize((220,220),Image.ANTIALIAS)
    # make a blank image for the text, initialized to transparent text color
    textes = Image.new('RGBA',(1024,512))
    # get a drawing context
    d = ImageDraw.Draw(textes)
    # draw text, half opacity
    o_x = 40
    o_y = 30
    fontlegendb = ImageFont.truetype("Montserrat-SemiBold.ttf", 20)
    fontlegend  = ImageFont.truetype("Montserrat-Regular.ttf", 16)
    legendx,legendy = (o_x+675,o_y+145)

    colors = ( (37,168,126,255),(226,61,33,255),(33,53,88,255),(187,187,187,255))
    _ly = legendy
    for i,pos in enumerate(('pour','contre','abstention','absent')):
        if positions['position']==pos:
            d.rectangle(((legendx-4,_ly),(legendx+24,_ly+28)),colors[i])
            d.text((legendx+30,_ly+2),"%s (%d)" % (pos,positions[pos]),font=fontlegendb,fill=(33,53,88,255))
            _ly += 34
        elif positions.get(pos,0)>0:
            d.rectangle(((legendx,_ly),(legendx+20,_ly+20)),colors[i])
            d.text((legendx+26,_ly),"%s (%d)" % (pos,positions[pos]),font=fontlegend,fill=(33,53,88,255))
            _ly += 26

    fontthemesize = 16

    fontnomsize=fst
    fontdossize=fs
    title = groupeslibs[groupe] if groupe else scrutin['theme']
    fonttheme = ImageFont.truetype("Montserrat-Bold.ttf", fontthemesize)
    themew,themeh = fonttheme.getsize(title)
    d.rectangle(((o_x,o_y), (themew+o_x+14, o_y+fontthemesize+12)), fill=(255,0,82,255))
    d.text((o_x+8,o_y+4), title, font=fonttheme, fill=(255,255,255,255))

    fontdos = ImageFont.truetype("Montserrat-Bold.ttf", fontdossize)

    nomw,nomh = fontdos.getsize(scrutin['dossier'])
    #d.rectangle(((o_x, o_y+fontthemesize+12), (nomw+o_x+8,o_y+fontthemesize+12+fontdossize+12)), fill=(33,53,88,255))
    #d.text((o_x+4,o_y+fontthemesize+16), scrutin['scrutin_dossierLibelle'], font=fontdos, fill=(255,255,255,255))



    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", fontnomsize)
    nom = scrutin['nom'].upper()


    def drawwrappedtext(img,txt,x,y,maxwidth,lineheight,font,color,eval=False):
        _y = y
        _x = x
        for word in txt.split(' '):
            wordw,wordh = font.getsize(word+' ')
            if _x+wordw>maxwidth:
                _x = x
                _y += lineheight
            if not eval:
                d.text((_x,_y), word+' ', font=font, fill=color)
            _x += wordw
        return _y + lineheight

    def drawjustifiedtext(img,txt,x,y,maxwidth,lineheight,fontbase,fontsize,color,eval=False):



        def fontsel(fontbase,fontsize,bold,italic):
            if bold:
                face = 'SemiBoldItalic' if italic else 'SemiBold'
            elif italic:
                face = 'Italic'
            else:
                face = 'Regular'

            return ImageFont.truetype(fontbase+'-'+face+'.ttf',fontsize)
        #txt = "ceci **est** un *test* "+txt+" et ceci **aussi** *est un test*"
        _words = []
        _y = y

        bold = False
        italic= False
        font = fontsel(fontbase,fontsize,bold,italic)
        lines = []
        line = []
        width = 0
        # remplacer les liens par du gras
        txt = re.sub(r'\[([^\]]+)\]\([^\)]+\)',r'**\1**',txt)

        for word in txt.split(' '):
            kw = word.replace(',','').replace(':','').replace('.','').replace(';','')
            if len(kw)==0:
                continue
            if len(kw)>2 and kw[0:2]=='**':
                bold = True
            elif kw[0]=='*' or kw[0]=='_':
                italic = True
            font = fontsel(fontbase,fontsize,bold,italic)
            _w = word.replace('*','').replace('_','')
            w = ' '+_w if len(line)>0 else _w
            ww,wh = font.getsize(w)
            if width+ww<=maxwidth:
                line.append((width,font,w))
                width += ww
            else:
                whitespace = float(maxwidth-width)/(len(line)-1)

                w1 = line[0]
                _line = [(0,w1[1],w1[2])]
                wsp = 0
                for it in line[1:]:
                    wsp += whitespace
                    _line.append((it[0]+wsp,it[1],it[2]))
                lines.append(_line)
                width,wh = font.getsize(_w)
                line = [(0,font,_w)]

            if len(kw)>2 and kw[-2:]=='**':
                bold = False
            elif kw[-1]=='*' or kw[-1]=='_':
                italic = False
            font = fontsel(fontbase,fontsize,bold,italic)

            #d.text((_x,_y),''.join(_words),font=font,fill=color)
        lines.append(line)

        for l in lines:
            for w in l:
                d.text((x+w[0],_y),w[2],font=w[1],fill=color)
            _y += lineheight

        return _y
    scrutin['dossier'] = scrutin['dossier'].replace('\t','')
    y = drawwrappedtext(eval=True,img=d,txt=scrutin['dossier'],x=o_x+8,y=o_y+fontthemesize+16+4, font=fontdos, maxwidth=512,lineheight=fontdossize+6,color=(255,255,255,255))
    d.rectangle(((o_x, o_y+fontthemesize+12), (min((nomw+o_x+14,512)),y+2)),fill=(33,53,88,255))
    y = 12+drawwrappedtext(img=d,txt=scrutin['dossier'],x=o_x+8,y=o_y+fontthemesize+18, font=fontdos, maxwidth=512,lineheight=fontdossize+6,color=(255,255,255,255))

    y = drawwrappedtext(img=d,txt=nom,font=fontnom,color=(33,53,88,255),x=o_x,y=y,maxwidth=512,lineheight=fontnomsize+4)
    #y = drawwrappedtext(img=d,txt=nom,font=fontnom,color=(33,53,88,255),x=o_x,y=o_y+10+fontthemesize+12+fontdossize+12+4,maxwidth=512,lineheight=fontnomsize+4)
    fontdesc = ImageFont.truetype("Montserrat-Regular.ttf", 16)
    drawjustifiedtext(img=d,txt=scrutin['desc'],x=o_x,y=y+10,maxwidth=480,lineheight=22,color=(33,53,88,255),fontbase='Montserrat',fontsize=16)
    vis.paste(imchart,(517,10),imchart)
    vis.paste(ccircle,(663,120),ccircle)
    vis.paste(textes,(0,0),textes)


    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()


def visuelvotecledetail(num,fs=32,fst=34):
    gpcolors = {'LAREM':(252,238,33,255),
                'MODEM':(247,147,30,255),
                'LR':(31,107,255,255),
                'UDI-AGIR':(0,178,244,255),
                'NI':(204,204,204,255),
                'NG':(255,21,152,255),
                'FI':(255,23,0,255),
                'GDR':(180,0,5,255)
                }

    scrutins_cles = use_cache('scrutins_cles',lambda:getScrutinsCles(),expires=3600)
    scrutins_positions = use_cache('scrutins_positions',lambda:getScrutinsPositions(),expires=36000)
    scrutin = mdb.scrutins.find_one({'scrutin_num':num})
    
    if not scrutin: #or not num in scrutins_cles:
        return ""
    scrutin.update(scrutins_cles.get(num,{}))
    if scrutin['scrutin_dossierLibelle']!='N/A':
        scrutin['dossier'] = scrutin['scrutin_dossierLibelle']
    scrutin['dossier'] = scrutin['dossier'].replace(u'\u0092',"'")


    #return json_response(positions)
    cercles = {'pour':[],'contre':[],'abstention':[]}

    for pos in ['pour','contre','abstention']:
        gprec = ""
        for g in [ u'LAREM', u'MODEM', u'FI',  u'GDR', u'NG',  u'LR', u'UDI-AGIR', u'NI'  ]:
            if scrutin['scrutin_positions'][g].get(pos,0):
                if not (gprec=='LAREM' and g==u'MODEM'):
                    cercles[pos].append(None)

                for c in range(scrutin['scrutin_positions'][g][pos]):
                    cercles[pos].append(gpcolors[g])

                gprec = g
    maxcercles = max([len(cercles[p]) for p in cercles.keys()])

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/visuelstat21clean'

    vis = Image.open(vispath+'/share_obs_clean_1x1b.png')

    textes = Image.new('RGBA',(1024,1024))
    # get a drawing context
    d = ImageDraw.Draw(textes)

    o_x = 60
    o_y = 30

    fontthemesize = 28

    fontnomsize=fst

    fontdossize=fs
    title = scrutin.get('theme','TEST')
    fonttheme = ImageFont.truetype("Montserrat-Bold.ttf", fontthemesize)
    themew,themeh = fonttheme.getsize(title)
    d.rectangle(((o_x,o_y), (themew+o_x+28, o_y+fontthemesize+24)), fill=(255,0,82,255))
    d.text((o_x+16,o_y+8), title, font=fonttheme, fill=(255,255,255,255))

    fontdos = ImageFont.truetype("Montserrat-Bold.ttf", fontdossize)

    nomw,nomh = fontdos.getsize(scrutin['dossier'])
    #d.rectangle(((o_x, o_y+fontthemesize+12), (nomw+o_x+8,o_y+fontthemesize+12+fontdossize+12)), fill=(33,53,88,255))
    #d.text((o_x+4,o_y+fontthemesize+16), scrutin['scrutin_dossierLibelle'], font=fontdos, fill=(255,255,255,255))



    fontnom = ImageFont.truetype("Montserrat-Bold.ttf", fontnomsize)
    nom = scrutin.get('nom','TEST2').upper()



    def drawwrappedtext(img,txt,x,y,maxwidth,lineheight,font,color,eval=False):
        _y = y
        _x = x
        for word in txt.split(' '):
            wordw,wordh = font.getsize(word+' ')
            if _x+wordw>maxwidth:
                _x = x
                _y += lineheight
            if not eval:
                d.text((_x,_y), word+' ', font=font, fill=color)
            _x += wordw
        return _y + lineheight

    scrutin['dossier'] = scrutin['dossier'].replace('\t','')
    y = drawwrappedtext(eval=True,img=d,txt=scrutin['dossier'],x=o_x+16,y=o_y+fontthemesize+32+4, font=fontdos, maxwidth=1024-o_x,lineheight=fontdossize+6,color=(255,255,255,255))
    d.rectangle(((o_x, o_y+fontthemesize+24), (1024-o_x,y+2)),fill=(33,53,88,255))
    y = 24+drawwrappedtext(img=d,txt=scrutin['dossier'],x=o_x+16,y=o_y+fontthemesize+32, font=fontdos, maxwidth=1024-o_x,lineheight=fontdossize+6,color=(255,255,255,255))

    y = drawwrappedtext(img=d,txt=nom,font=fontnom,color=(33,53,88,255),x=o_x,y=y,maxwidth=1024-o_x,lineheight=fontnomsize+4)

    # cercles
    # 577
    config = [
        [100,dict(c_by_row=10,c_r=22,c_margin=0.25)],
        [200,dict(c_by_row=12,c_r=19,c_margin=0.25)],
        [300,dict(c_by_row=14,c_r=16,c_margin=0.25)],
        [400,dict(c_by_row=16,c_r=14,c_margin=0.25)],
        [500,dict(c_by_row=18,c_r=12,c_margin=0.3)],
        [600,dict(c_by_row=20,c_r=11,c_margin=0.35)]


    ]

    def draw_circles(_circles, c_by_row,c_r,c_margin):
        #c_by_row = 20
        #c_r = 12
        factor = 4
        c_margin = int(c_r * c_margin * factor)
        c_r = int(c_r * factor)
        _y = 0
        circles = []
        i = 0
        for c in _circles:
            _x = i % c_by_row
            _y = int(i/c_by_row)
            if c:
                circles.append(c)
                i += 1
            elif _x != 0:
                circles += [(255,255,255,0)] * (c_by_row-_x)
                i += c_by_row-_x

        positions = Image.new('RGB',(int(factor*1000),int(factor*1000)),color=(255,255,255))
        posdraw = ImageDraw.Draw(positions)
        nl_y = 0
        last = None
        for i,c in enumerate(circles):
            _x = i % c_by_row
            _y = int(i/c_by_row)

            if c != (255,255,255,0):
                if c != last and c!=gpcolors['MODEM']:
                    nl_y += 2 * c_margin
                last = c
            posdraw.ellipse((_x*(c_r+c_margin),nl_y+_y*(c_r+c_margin),c_r+_x*(c_r+c_margin),c_r+nl_y+_y*(c_r+c_margin)),fill=c)

        return positions.resize((1000,1000),Image.ANTIALIAS).crop((0,0,1000,600))

    c_cfg = {}
    for cfg in config:
        if maxcercles<cfg[0]:
            c_cfg = cfg[1]
            break

    colwidth = c_cfg['c_by_row'] * ( c_cfg['c_r'] + (int(c_cfg['c_margin']*c_cfg['c_r']))) - (int(c_cfg['c_margin']*c_cfg['c_r']))

    colspace = (1024-2*o_x-3*colwidth)/2
    for i,pos in enumerate(['pour','contre','abstention']):
        img = draw_circles(cercles[pos],**c_cfg)
        vis.paste(img,(o_x+i*(colwidth+colspace),60+y))


    legend = [
        [ ('LR',[u'Les Républicains']), ('UDI-AGIR',['UDI-AGIR et Ind.']), ('NI',['Non inscrits'])],
        [ ('LAREM',[u'La République',u'en Marche']), ('MODEM',[u'Modem']) ],
        [ ('NG',[u'Nouvelle Gauche']), ('FI',[u'La France Insoumise']),('GDR',[u'Gauche Démocrate',u'et Républicaine'])]
    ]

    fontposb = ImageFont.truetype("Montserrat-SemiBold.ttf", 27)
    fontpos  = ImageFont.truetype("Montserrat-Regular.ttf", 27)

    # votes
    for col, pos in enumerate(['Pour','Contre','Abstention']):
        d.text((o_x+col*(colwidth+colspace),y+20), pos, font=fontpos, fill=(33,53,88,255))
        pw,ph = fontpos.getsize(pos)
        d.text((pw+10+o_x+col*(colwidth+colspace),y+20), "(%s)" % scrutin['scrutin_positions']['assemblee'].get(pos.lower(),0), font=fontposb, fill=(33,53,88,255))


    # legende
    legendimg = Image.new('RGB',(2048,290),color=(255,255,255))
    legenddraw = ImageDraw.Draw(legendimg)
    leg_fs = 44
    fontpos2  = ImageFont.truetype("Montserrat-Regular.ttf", leg_fs)
    for col, colleg in enumerate(legend):
        for row,leg in enumerate(colleg):
            legenddraw.ellipse((col*2*(colwidth+colspace),leg_fs/2+row*90,col*2*(colwidth+colspace)+leg_fs,leg_fs/2+leg_fs+row*90),gpcolors[leg[0]])
            for i,l in enumerate(leg[1]):
                legenddraw.text((col*2*(colwidth+colspace)+70,leg_fs/2+row*90+(i*leg_fs)-8-(leg_fs/2)*(len(leg[1])-1)),l, font=fontpos2, fill=(33,53,88,255))
    legimg = legendimg.resize((1024,145),Image.ANTIALIAS).crop((0,0,1024,145))
    vis.paste(legimg,(o_x,780))

    #d.ellipse((25,25+y, 50, 50+y), fill=(255,0,0,255))

    #y = drawwrappedtext(img=d,txt=nom,font=fontnom,color=(33,53,88,255),x=o_x,y=o_y+10+fontthemesize+12+fontdossize+12+4,maxwidth=512,lineheight=fontnomsize+4)
    fontdesc = ImageFont.truetype("Montserrat-Regular.ttf", 16)

    vis.paste(textes,(0,0),textes)


    final = vis
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
