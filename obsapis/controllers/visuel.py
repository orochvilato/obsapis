# -*- coding: utf-8 -*-

from PIL import Image

vis = Image.open('fiche_fond.png')
poster = Image.open('fiche_poster.png')
plis = Image.open('fiche_plis.png')
footer = Image.open('fiche_macaron_footer.png')
vis.paste(poster,(0,0),poster)
vis.paste(plis,(0,0),plis)
vis.paste(footer,(0,0),footer)
vis.save('visuel.png')
