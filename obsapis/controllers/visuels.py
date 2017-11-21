# -*- coding: utf-8 -*-
from obsapis import app

from selenium import webdriver
from PIL import Image
import StringIO

factor = 1.2
def get_visuel(depute):
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    options.add_argument('window-size=1000x1000')
    options.add_argument('force-device-scale-factor=1.2')
    driver = webdriver.Chrome(chrome_options=options)
    #driver = webdriver.PhantomJS() # or add to your PATH
    #driver.set_window_size(1600, 1024) # optional
    driver.get("http://dev.observatoire-democratie.fr/assemblee/deputes/recherche?requete=bergé")

    import os

    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','obs1'])

    image = Image.open(StringIO.StringIO(driver.get_screenshot_as_png()))
    image3 = image.crop((120*factor,560*factor,860*factor,804*factor))
    #image3 = image2.resize((975,305))
    output = StringIO.StringIO()
    vis = Image.open(path+'/fiche_fond.png').resize((1024,1024))
    poster = Image.open(path+'/fiche_poster.png').resize((1024,1024))
    plis = Image.open(path+'/fiche_plis.png').resize((1024,1024))
    footer = Image.open(path+'/fiche_macaron_footer_neutre.png').resize((1024,1024))
    vis.paste(poster,(0,0),poster)
    vis.paste(image3,(70,170))
    vis.paste(plis,(0,0),plis)
    vis.paste(footer,(0,0),footer)
    #final = vis.resize((1024,1024))
    vis.save(output,'PNG')
    return output.getvalue()