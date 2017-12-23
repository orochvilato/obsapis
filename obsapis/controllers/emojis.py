# -*- coding: utf-8 -*-
from obsapis import app
import base64
from PIL import Image
path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets','emojis'])

bases = {'emojis2': {'base':Image.open(path+'/emoji2.png'),'items':[]},
         'emojis1': {'base':Image.open(path+'/emoji1.png'),
                     'items':['grinning','grimacing','grin','joy','smiley','smile','sweat_smile','laughing','innocent','wink',
                              'blush','slight_smile','upside_down','relaxed','yum','relieved','heart_eyes','kissing_heart','kissing',
                              'kissing_smiling_eyes','kissing_closed_eyes','stuck_out_tongue_winking_eye','stuck_out_tongue_closed_eyes',
                              'stuck_out_tongue','money_mouth','nerd','sunglasses','hugging','smirk','no_mouth','neutral_face','expressionless',
                              'unamused','rolling_eyes','thinking','flushed','disappointed','worried','angry','rage','pensive','confused',
                              'slight_frown','frowning2','persevere','confounded','tired_face','weary','triumph','open_mouth','scream',
                              'fearful','cold_sweat','hushed','frowning','anguished','cry','disappointed_relieved','sleepy','sweat','sob','dizzy_face',
                              'astonished','zipper_mouth','mask','thermometer_face','head_bandage','sleeping','zzz','poop' ]}
        }
defs = {}
for base,basedef in bases.iteritems():
    for i,item in enumerate(basedef['items']):
        defs[item] = {'base':base,'x':44*(i % 42),'y':44*(i/42)}

def get_emojis_css(emojis,size=22):
    from string import Template

    templ_css = Template("""
        .${emoji} {
            background: url(data:image/png;base64,${emoji64}) no-repeat left center;
            background-size: 100%;
            display: inline-block;
            margin-bottom:-${margin}px;
            width: ${size}px;
            height: ${size}px;
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
        css.append(templ_css.substitute(emoji=e,emoji64=emoji64,size=size-4,margin=2))

    return '\n'.join(css)
