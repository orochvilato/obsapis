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

    # make a blank image for the text, initialized to transparent text color
    textes = Image.new('RGBA',(2000,2000))
    d = ImageDraw.Draw(textes)
    margin_bottom = int(params['margin_bottom']) #60
    margin_top = int(params['margin_top']) #684
    margin_left = int(params['margin_left']) #170
    w = 2000-2*margin_left
    h = 2000-margin_top-margin_bottom
    inity = margin_top
    initx = margin_left

    border = int(params['border']) #5
    cols = int(params['cols']) #4
    rows = int(params['rows']) #5
    spacing = int(params['spacing']) # 25
    case_w = (w - (cols-1) * spacing) / cols
    case_h = (h - (rows-1) * spacing) / rows
    for col in range(cols):
        x = initx + col*(case_w+spacing)
        for row in range(rows):
            y = inity + row*(case_h+spacing)
            d.rectangle(((x,y), (x+case_w,y+case_h)), fill=(255,255,255,200))
            for b in range(border):
                d.rectangle(((x+b,y+b), (x+case_w-b,y+case_h-b)), outline=(0,0,0,255))

    # get a drawing context

    # draw text, half opacity

    #fontcirco = ImageFont.truetype("Montserrat-Bold.ttf", 19)
    #circ_w,circ_h = fontcirco.getsize(circo)
    #circ_pad = (h - circ_h)/2
    #circ_x,circ_y = 12+photo.size[1],100
    #
    #d.text((circ_x+6,circ_y+circ_pad), circo, font=fontcirco, fill=(255,255,255,255))

    fondcouleur.paste(texture,(0,0),texture)
    fondcouleur.paste(bingo,(0,0),bingo)
    fondcouleur.paste(logo_emission,(0,0),logo_emission)
    fondcouleur.paste(textes,(0,0),textes)

    final = fondcouleur
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
