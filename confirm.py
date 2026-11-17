import json, re, time, signal, re2
exec(open('analyze.py').read().split('res=[]')[0].replace("corpus=json.load(open('corpus.json'))","corpus=[]"))
R=json.load(open('analysis.json'))
hits=[r for r in R if r.get('dyn')=='pol']
out=[]
for i,r in enumerate(hits):
    pat=r['pattern']; c,suf=r['dyn_desc']
    rx=re.compile(pat)
    try: r2=re2.compile(pat)
    except Exception: r2=None
    row={'id':i+1,'pattern':pat,'origins':r['origins'],'suspect':r['suspect'],'pump':c,'suf':suf}
    for name,fn in (('search',rx.search),('match',rx.match)):
        d={}
        for n in (1000,2000,4000,8000):
            t=timed(lambda: fn(c*n+suf),3.0); d[n]=t
            if t is None: break
        row[name]=d
    d={}
    for n in ((8000,100000,1000000) if r2 else ()):
        t=timed(lambda: r2.search(c*n+suf),5.0); d[n]=t
    row['re2']=d
    out.append(row)
json.dump(out,open('confirm.json','w'),default=str)
for o in out:
    print(o['id'],o['origins'],repr(o['pattern'])[:70],'| search',{k:(None if v is None else round(v,3)) for k,v in o['search'].items()},'| match',{k:(None if v is None else round(v,3)) for k,v in o['match'].items()},'| re2',{k:(None if v is None else round(v,4)) for k,v in o['re2'].items()})
