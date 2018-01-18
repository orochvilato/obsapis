from obsapis import obspath
import os
import os.path
import json

path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

output_path = os.path.join(path,'data')

def launchScript(name,params=""):
    fp = obspath + '/.pyenv/bin/python '+os.path.join(path,'scripts', name+'.py')+' '+output_path+' '+params
    print fp
    did_scrape = True if os.system(fp) else False

    return did_scrape

def getData(name,id):
    fp = os.path.join(request.folder, 'private/data/', name +'.csv')
    with open(fp) as csvfile:
        reader = csv.DictReader(csvfile,delimiter='|')
        result = dict((row[id].decode('utf8'),dict((k,v.decode('utf8')) for k,v in row.iteritems())) for row in reader)
    return result
def addData(name,elts):
    fp = os.path.join(request.folder, 'private/data/', name +'.csv')
    with open(fp,'a') as f:
        f.write('|'.join([e.encode('utf8') for e in elts])+'\n')

def getJson(name):
    return json.loads(open(os.path.join(output_path,name+'.json'),'r').read())
