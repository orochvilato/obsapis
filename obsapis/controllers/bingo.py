import StringIO
from PIL import Image,ImageFont,ImageDraw
from obsapis import app

def bingovisuel(params):

    print params
    from base64 import b64decode

    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/bingo'

    bingo = Image.open(vispath+'/bingo.png')
    fondcouleur = Image.open(vispath+'/fondcouleur.png')
    logo_emission = Image.open(vispath+'/logo_emissionpolitique.png')
    texture = Image.open(vispath+'/texture.png')
    wordstr = params['mots']
    # make a blank image for the text, initialized to transparent text color
    fond = Image.new('RGB',(2000,2000),(0,0,0))
    textes = Image.new('RGBA',(2000,2000),(255,255,255,0))
    d = ImageDraw.Draw(textes)
    margin_bottom = int(params['margin_bottom']) #60
    margin_top = int(params['margin_top']) #684
    margin_left = int(params['margin_left']) #170
    w = 2000-2*margin_left
    h = 2000-margin_top-margin_bottom
    inity = margin_top
    initx = margin_left
    words = wordstr.split('\n')
    border = int(params['border']) #5
    cols = int(params['cols']) #4
    rows = int(params['rows']) #5
    fontsize = int(params['fontsize']) #100
    spacing = int(params['spacing']) # 25
    case_w = (w - (cols-1) * spacing) / cols
    case_h = (h - (rows-1) * spacing) / rows
    inner_margin = int(params['inner_margin']) #20
    interline = float(params['interline'])/100 #120
    transparence_case = int(params['transparence_case'])
    for col in range(cols):
        x = initx + col*(case_w+spacing)
        for row in range(rows):
            _word = words[col*rows+row].split(';')
            word = _word[0]
            transp = 255 if len(_word)>1 else transparence_case


            y = inity + row*(case_h+spacing)
            d.rectangle(((x,y), (x+case_w,y+case_h)), fill=(255,255,255,transp))
            for b in range(border):
                d.rectangle(((x+b,y+b), (x+case_w-b,y+case_h-b)), outline=(0,0,0,255))

            fs = fontsize

            ok = False
            while not ok:
                font = ImageFont.truetype("Roboto-Bold.ttf", fs)
                eval_w = 0
                eval_h = 0
                for l in word.split('|'):
                    wd_w,wd_h = font.getsize(l)
                    eval_w = max(wd_w,eval_w)
                    eval_h += wd_h*interline
                if eval_w + 2 * inner_margin < case_w and eval_h + 2* inner_margin < case_h:
                    ok = True
                fs -= 1
            _h = 0
            for l in word.split('|'):
                wd_w,wd_h = font.getsize(l)
                d.text((x + (case_w-wd_w)/2,y + _h + (case_h-eval_h)/2), l, font=font, fill=(0,0,0,255))
                _h += wd_h*interline

    # get a drawing context

    # draw text, half opacity

    #circ_w,circ_h = fontcirco.getsize(circo)
    #circ_pad = (h - circ_h)/2
    #circ_x,circ_y = 12+photo.size[1],100
    #
    #d.text((circ_x+6,circ_y+circ_pad), circo, font=fontcirco, fill=(255,255,255,255))

    fond.paste(fondcouleur,(0,0),fondcouleur)
    fond.paste(texture,(0,0),texture)
    fond.paste(bingo,(0,0),bingo)
    fond.paste(logo_emission,(0,0),logo_emission)
    fond.paste(textes,(0,0),textes)

    final = fond
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
