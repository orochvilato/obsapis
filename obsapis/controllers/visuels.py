# -*- coding: utf-8 -*-
from obsapis import app,mdb
from obsapis.tools import json_response,getdot
import requests
from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image,ImageFont,ImageDraw
import StringIO
import datetime

def maxis():
    maxcirco = []
    maxnom = []
    maxgp = []
    for dep in mdb.deputes.find({},{'depute_shortid':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}):
        id = dep['depute_shortid']
        if dep['depute_region']==dep['depute_departement']:
            circo =  "%s (999) / %se circ" % (dep['depute_departement'],dep['depute_circo'])
        else:
            circo =  "%s / %s (999) / %se circ" % (dep['depute_region'],dep['depute_departement'],dep['depute_circo'])
        maxcirco.append((id,len(circo)))
        maxnom.append((id,len(dep['depute_nom'])))
        gp = "%s (%s)" % (dep['groupe_libelle'],dep['groupe_abrev'])
        maxgp.append((id,len(gp)))
        maxcirco.sort(key=lambda x:x[1],reverse=True)
        maxnom.sort(key=lambda x:x[1],reverse=True)
        maxgp.sort(key=lambda x:x[1],reverse=True)
    return dict(circo=maxcirco[:10],nom=maxnom[:10],gp=maxgp[:10])

def genvisuelstat(depute,stat):
    params = {'participation':{'field':'stats.positions.exprimes','label':['Participation aux','scrutins publics']},
              'commission':{'field':'stats.commissions.present','label':['Présence en','commission']},
              'absent':{'field':'stats.positions.absent','label':['Absence lors des','scrutins publics']}
              }
    fields = {'depute_photo':1,'depute_naissance':1,'groupe_abrev':1,'groupe_libelle':1,'depute_departement':1,'depute_region':1,'depute_circo':1,'depute_nom':1,'_id':None}
    fields.update(dict((p['field'],1) for p in params.values()))
    dep = mdb.deputes.find_one({'depute_shortid':depute},fields)

    if not dep or not stat in params.keys():
        return "nope"
    if dep['depute_region']==dep['depute_departement']:
        circo =  "%s (999) / %se circ" % (dep['depute_departement'],dep['depute_circo'])
    else:
        circo =  "%s / %s (999) / %se circ" % (dep['depute_region'],dep['depute_departement'],dep['depute_circo'])
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
    footer = Image.open(vispath+'/obs_share_square_footer.png')

    statimage = Image.open(path+'/assets/%s/%d.png' % (stat,int(getdot(dep,params[stat]['field'])))).resize((300,300),Image.ANTIALIAS)

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

    fontlabel = ImageFont.truetype("Montserrat-Bold.ttf", 34)
    for i,l in enumerate(params[stat]['label']):
        d.text((660,282+i*45),l.decode('utf8'), font=fontlabel,fill=(130,205,226,255))

    fontgen = ImageFont.truetype("Montserrat-Regular.ttf", 11)
    dategen = 'Généré le %s' % datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')
    d.text((840,570),dategen.decode('utf8'),font=fontgen,fill=(10,10,10,255))

    vis.paste(poster,(0,0),poster)
    vis.paste(textes,(0,0),textes)
    vis.paste(photo,(70,139))
    vis.paste(statimage,(340,220))
    vis.paste(plis,(0,0),plis)
    vis.paste(footer,(0,0),footer)
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
