# -*- coding: utf-8 -*-
from obsapis import app,mdb

from selenium import webdriver
from selenium.webdriver.chrome import service
from PIL import Image
import StringIO

def get_visuel(id,depute,regen=None):

    dep = mdb.deputes.find_one({'depute_shortid':depute},{'depute_nom':1,'_id':None})
    if not dep:
        return "nope"
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels',id])
    imgpath = path+'/tous/'+depute+'.png'
    import os.path
    if os.path.isfile(imgpath) and not regen:
        return open(imgpath).read()

    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    if id=='obs1':
        factor = 1.2
        url = "http://dev.observatoire-democratie.fr/assemblee/deputes/recherche?requete=%s" % dep['depute_nom']
        zone = (120,560,860,804)
        size = '1000x1000'

    else:
        factor = 1
        url = "http://dev.observatoire-democratie.fr/assemblee/deputes/%s/votes" % depute
        zone = (90,310,840,570)
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
        footer = Image.open(path+'/fiche_macaron_footer.png').resize((1024,1024))

        vis.paste(poster,(0,0),poster)
        vis.paste(image3,(70,170))
        vis.paste(plis,(0,0),plis)
        vis.paste(footer,(0,0),footer)
        final = vis
    else:
        width, height = image2.size
        image3 = image2.resize((680,int(680*float(height)/width)),Image.ANTIALIAS)
        #image3 = image2
        vis = Image.open(path+'/share_2_1_fond.png') #.resize((1024,512))
        poster = Image.open(path+'/share_2_1_poster.png') #.resize((1024,512))
        plis = Image.open(path+'/share_2_1_plis.png') #.resize((1024,512))
        footer = Image.open(path+'/share_2_1_footer.png') #.resize((1024,512))
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
