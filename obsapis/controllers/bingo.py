import StringIO
from PIL import Image,ImageFont,ImageDraw,ImageOps

from obsapis import app

def bingovisuel(params,files):

    import numpy
    import cv2
    import sys



    from base64 import b64decode
    output = StringIO.StringIO()
    path = '/'.join(app.instance_path.split('/')[:-1] +['obsapis','resources','visuels'])
    vispath = path+'/bingo'

    bingo = Image.open(vispath+'/bingo.png')
    fondcouleur = Image.open(vispath+'/fondcouleur.png')
    logo_emission = Image.open(vispath+'/logo_emission_politique.png')
    logo_emission = Image.open(vispath+'/logo_bourdin_direct.jpg')
    logo_emission = Image.open(vispath+'/logo_onpc.png')

    texture = Image.open(vispath+'/texture.png')


    cascPath = "/haarcascade_frontalface_default.xml"
    med1 = files['medaillon1_file']
    med2 = files['medaillon2_file']
    medaillons_cover = int(params['medaillons_cover']) #.180
    faces = []
    medaillons = []
    if med1.filename:
        med1f = StringIO.StringIO()
        med1.save(med1f)
        med1f.seek(0)
        face1 = Image.open(med1f)
        facefactor = int(params['medaillon1_spacearound_pct']) #.180
        facerotation = int(params['medaillon1_rotation']) #25
        faceborder = int(params['medaillon1_border'])#15
        leftshift = int(params['medaillon1_leftshift_pct'])#15
        faces.append((face1,numpy.array(face1.convert('RGB')),facefactor,facerotation,faceborder,leftshift))
    if med2.filename:
        med2f = StringIO.StringIO()
        med2.save(med2f)
        med2f.seek(0)
        face2 = Image.open(med2f)
        facefactor = int(params['medaillon2_spacearound_pct']) #.180
        facerotation = int(params['medaillon2_rotation']) #25
        faceborder = int(params['medaillon2_border'])#15
        leftshift = int(params['medaillon2_leftshift_pct'])#15
        faces.append((face2,numpy.array(face2.convert('RGB')),facefactor,facerotation,faceborder,leftshift))

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(vispath+cascPath)

    # Read the image
    #image = cv2.imread(vispath+'/face2.jpg')
    #image = Image.open('Image.jpg').convert('RGB')
    for fimage,cvface,facefactor,facerotation,faceborder,leftshift in faces:
        gray = cv2.cvtColor(cvface, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        detectfaces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
            #flags = cv2.CV_HAAR_SCALE_IMAGE
            )
        if len(detectfaces):
            fx, fy, fw, fh = detectfaces[0]
            centerx = int(fx+float(100+leftshift)/200*fw)
            centery = int(fy+fh/2)
            neww = int(max(fw,fh)*float(facefactor)/100)

            #face = Image.open(vispath+'/face2.jpg')
            face = fimage.crop((centerx-int(neww/2),centery-int(neww/2),centerx+int(neww/2),centery+int(neww/2)))
            face = face.resize((265,265), Image.ANTIALIAS).rotate(facerotation)
            facew,faceh = face.size
            red = Image.new('RGB',(facew+2*faceborder,faceh+2*faceborder),(255,0,0))
            mask = Image.new('L',red.size,0 )
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + mask.size, fill=255)
            red.putalpha(mask)

            mask = Image.new('L',face.size,0 )
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + mask.size, fill=255)
            face.putalpha(mask)
            red.paste(face,(faceborder,faceborder),face)

            #red = red.resize((265,265), Image.ANTIALIAS).rotate(facerotation)
            medaillons.append(red)


    medy = 20
    medx = 1650-(265-medaillons_cover)*(len(medaillons)-1)
    for medaillon in medaillons:
        bingo.paste(medaillon,(medx,medy),medaillon)
        medx = medx + (265-medaillons_cover)
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
    logow,logoh = logo_emission.size
    factor = min(float(270)/logoh,float(1900)/logow)
    print factor, logow*factor, logoh*factor
    logo_emission_new = logo_emission.resize((int(logow*factor),int(logoh*factor)),Image.ANTIALIAS)
    fond.paste(logo_emission_new,((2000-int(logow*factor))/2,20+(270-int(logoh*factor))/2))
    fond.paste(textes,(0,0),textes)

    final = fond
    final.save(output,'PNG')
    #final.save(imgpath,'PNG')
    return output.getvalue()
