# -*- coding: utf-8 -*-
from obsapis import app
import base64
from PIL import Image
path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels','assets','emojis'])

bases = {'emojis2': {'base':Image.open(path+'/emoji2.png'),
                     'ipl':10,
                     'size':44,
                     'items':['raised_hands','clap','wave','thumbsup','thumbsdown','punch','fist','v','ok_hand','raised_hand','open_hands',
                              'muscle','pray','point_up','point_up_2','point_down','point_left','point_right','middle_finger','hand_splayed',
                              'metal','vulcan','writing_hand','nail_care','ear','nose',':baby','boy','girl','man','woman','person_with_blond_hair','older_man',
                              'older_woman','man_with_gua_pi_mao','man_with_turban','cop','construction_worker','guardsman','spy','santa','angel','princess',
                              'bride_with_veil','walking','runner','dancer','bow','information_desk_person','no_good','ok_woman','raising_hand','person_with_pouting_face',
                              'person_frowning','haircut','massage','prince','man_in_tuxedo','mrs_claus','face_palm','shrug','pregnant_woman','selfie','man_dancing','call_me',
                              'raised_back_of_hand','left_facing_fist','right_facing_fist','fingers_crossed' 
                               ]},
         'emojis1': {'base':Image.open(path+'/emoji1.png'),
                     'ipl':42,
                     'size':44,
                     'items':['grinning','grimacing','grin','joy','smiley','smile','sweat_smile','laughing','innocent','wink',
                              'blush','slight_smile','upside_down','relaxed','yum','relieved','heart_eyes','kissing_heart','kissing',
                              'kissing_smiling_eyes','kissing_closed_eyes','stuck_out_tongue_winking_eye','stuck_out_tongue_closed_eyes',
                              'stuck_out_tongue','money_mouth','nerd','sunglasses','hugging','smirk','no_mouth','neutral_face','expressionless',
                              'unamused','rolling_eyes','thinking','flushed','disappointed','worried','angry','rage','pensive','confused',
                              'slight_frown','frowning2','persevere','confounded','tired_face','weary','triumph','open_mouth','scream',
                              'fearful','cold_sweat','hushed','frowning','anguished','cry','disappointed_relieved','sleepy','sweat','sob','dizzy_face',
                              'astonished','zipper_mouth','mask','thermometer_face','head_bandage','sleeping','zzz','poop',
                              'smiling_imp','imp','japanese_ogre','japanese_goblin','skull','ghost','alien','robot','smiley_cat','smile_cat','joy_cat',
                              'heart_eyes_cat','smirk_cat','kissing_cat','scream_cat','crying_cat_face','pouting_cat','lips',
                              'tongue','eye','eyes','bust_in_silhouette','busts_in_silhouette','speaking_head','dancers','couple',
                              'two_men_holding_hands','two_women_holding_hands','couple_with_heart','couple_ww','couple_mm','couplekiss','kiss_ww','kiss_mm',
                              'family','family_mwg','family_mwgb','family_mwbb','family_mwgg','family_wwb','family_wwg','family_wwgb','family_wwbb'
                              'family_wwgg','family_mmb','family_mmg','family_mmgb','family_mmbb','family_mmgg'
                               ]}
        }
defs = {}
for base,basedef in bases.iteritems():
    for i,item in enumerate(basedef['items']):
        defs[item] = {'base':base,'x':basedef['size']*(i % basedef['ipl']),'y':basedef['size']*(i/basedef['ipl'])}

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
        if e in defs.keys():
            de = defs[e]
        else:
            de = defs['middle_finger']
        emoji = bases[de['base']]['base'].crop((de['x'],de['y'],de['x']+44,de['y']+44))
        output = StringIO.StringIO()
        emoji.save(output,'PNG')
        emoji64 = base64.b64encode(output.getvalue())
        output.close()
        css.append(templ_css.substitute(emoji=e,emoji64=emoji64,size=size-4,margin=2))

    return '\n'.join(css)
