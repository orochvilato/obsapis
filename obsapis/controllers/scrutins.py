
def getScrutinsCles():
    from openpyxl import load_workbook
    from cStringIO import StringIO
    import requests

    r =requests.get("https://docs.google.com/spreadsheets/d/1lZ5aMIaglRh6_BK66AYkXzi9guJaMij9RlpSoO4dnIw/export?format=xlsx&id=1lZ5aMIaglRh6_BK66AYkXzi9guJaMij9RlpSoO4dnIw")
    f = StringIO(r.content)
    wb = load_workbook(f)
    ws = wb[wb.sheetnames[0]]
    elts = []
    for j,row in enumerate(ws.iter_rows(min_row=2)):
        elts.append([a.value for a in row])
    scles = {}
    for e in elts:
        if e[0] != None:
            scles[int(e[0])] = dict(num=int(e[0]),nom=e[1],desc=e[2],theme=e[3],lien=e[4])
    return scles
