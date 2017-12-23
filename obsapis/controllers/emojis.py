# -*- coding: utf-8 -*-
from obsapis import app
import base64
from PIL import Image
path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets','emojis'])

bases = {'emojis2': {'base':Image.open(path+'/emoji2.png'),'items':[]},
         'emojis1': {'base':Image.open(path+'/emoji1.png'),
                     'items':['grinning','grimacing','grin','joy','smiley','smile','sweat_smile','laughing','innocent','wink']}
        }
defs = {}
for base,basedef in bases.iteritems():
    for i,item in enumerate(basedef['items']):
        defs[item] = {'base':base,'x':44*(i % 44),'y':44*(i/44)}

def get_emojis_css(emojis):
    from string import Template

    templ_css = Template("""
        .${emoji} {
            background: url(data:image/png;base64,${emoji64}) no-repeat left center;
            background-size: 100%;
            display: inline-block;
            width: 22px;
            height: 22px;
        }""")
    css=[]

    import StringIO
    for e in emojis:
        de = defs[e]
        emoji = bases[de['base']]['base'].crop((de['x'],de['y'],de['x']+44,de['y']+44))
        output = StringIO.StringIO()
        emoji.save(output,'PNG')
        emoji64 = base64.b64encode(output.getvalue())
        output.close()
        css.append(templ_css.substitute(emoji=e,emoji64=emoji64))
    print css
    return '\n'.join(css)
