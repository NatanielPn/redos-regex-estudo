import re, json, signal, time, random, sys
import re._parser as P, re._constants as C
import re2
corpus=json.load(open('corpus.json'))

# ---------- analise estatica ----------
UNB=C.MAXREPEAT
def walk(sub, depth_unb, info):
    for op,av in sub:
        if op in (C.MAX_REPEAT,C.MIN_REPEAT,C.POSSESSIVE_REPEAT):
            lo,hi,body=av
            unb = hi==UNB or hi>=1000
            if unb and depth_unb>=1: info['nested']=True
            if unb:
                # alternancia sob repeticao?
                for o,a in body:
                    if o==C.BRANCH: info['alt_under_star']=True
            walk(body, depth_unb+(1 if unb else 0), info)
        elif op==C.SUBPATTERN:
            walk(av[3], depth_unb, info)
        elif op==C.BRANCH:
            for b in av[1]: walk(b, depth_unb, info)
        elif op in (C.ASSERT,C.ASSERT_NOT):
            info['lookaround']=True; walk(av[1], depth_unb, info)
        elif op==C.GROUPREF or op==C.GROUPREF_EXISTS:
            info['backref']=True
        elif op==C.ATOMIC_GROUP:
            info['atomic']=True; walk(av, depth_unb, info)
def static(pat):
    info={'nested':False,'alt_under_star':False,'lookaround':False,'backref':False,'atomic':False}
    try: tree=P.parse(pat)
    except Exception: return None
    walk(tree, 0, info)
    return info

# ---------- caracteres de bombeamento ----------
def sample_chars(sub, acc):
    for op,av in sub:
        if op==C.LITERAL: acc.append(chr(av))
        elif op==C.NOT_LITERAL: acc.append('a' if av!=ord('a') else 'b')
        elif op==C.ANY: acc.append('a')
        elif op==C.IN:
            for o,a in av:
                if o==C.LITERAL: acc.append(chr(a))
                elif o==C.RANGE: acc.append(chr(a[0]))
                elif o==C.CATEGORY:
                    acc.append({C.CATEGORY_DIGIT:'0',C.CATEGORY_SPACE:' ',C.CATEGORY_WORD:'a',C.CATEGORY_NOT_DIGIT:'a',C.CATEGORY_NOT_SPACE:'a',C.CATEGORY_NOT_WORD:'-'}.get(a,'a'))
                elif o==C.NEGATE: pass
        elif op in (C.MAX_REPEAT,C.MIN_REPEAT,C.POSSESSIVE_REPEAT): sample_chars(av[2],acc)
        elif op==C.SUBPATTERN: sample_chars(av[3],acc)
        elif op==C.BRANCH:
            for b in av[1]: sample_chars(b,acc)
        elif op==C.CATEGORY:
            acc.append({C.CATEGORY_DIGIT:'0',C.CATEGORY_SPACE:' ',C.CATEGORY_WORD:'a'}.get(av,'a'))
def pumps(pat):
    acc=[]
    try: sample_chars(P.parse(pat),acc)
    except Exception: pass
    seen=[]
    for c in acc+['a',' ','0']:
        if c not in seen and c.isprintable(): seen.append(c)
    return seen[:6]

class TO(Exception): pass
def _h(s,f): raise TO()
signal.signal(signal.SIGALRM,_h)
def timed(fn, limit):
    t=time.perf_counter()
    signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        fn(); ok=True
    except TO: ok=False
    finally: signal.setitimer(signal.ITIMER_REAL,0)
    return (time.perf_counter()-t) if ok else None

def probe(pat):
    """devolve (classe, melhor_texto_descr, dados) ; classe in {exp,pol,none}"""
    rx=re.compile(pat)
    best=None
    for c in pumps(pat):
        for suf in ['\x01','!','\n']:
            # exponencial: n pequeno
            ts={}
            stop=False
            for n in (16,22,28):
                t=timed(lambda: rx.search(c*n+suf),1.0)
                ts[n]=t
                if t is None: break
            if ts.get(28) is None or (ts.get(22) and ts.get(28) and ts[28]/max(ts[22],1e-6)>8 and ts[28]>0.05):
                return 'exp',(c,suf),ts
            # polinomial: n grande
            tp={}
            for n in (2000,8000):
                t=timed(lambda: rx.search(c*n+suf),2.0)
                tp[n]=t
                if t is None: break
            if tp.get(8000) is None or (tp[8000] and tp[8000]>0.5):
                if best is None: best=('pol',(c,suf),tp)
    if best: return best
    return 'none',None,None

res=[]
random.seed(7)
t0=time.time()
for i,r in enumerate(corpus):
    pat=r['pattern']
    st=static(pat)
    if st is None: continue
    rec={'pattern':pat,'origins':r['origins'],'static':st}
    # re2 compativel?
    try: re2.compile(pat); rec['re2_ok']=True
    except Exception: rec['re2_ok']=False
    suspect=st['nested'] or st['alt_under_star']
    rec['suspect']=suspect
    res.append(rec)
print('estaticas',len(res),flush=True)
# dinamico: todos os suspeitos + amostra de 80 nao suspeitos
sus=[r for r in res if r['suspect']]
non=[r for r in res if not r['suspect']]
sample=non
for k,r in enumerate(sus+sample):
    cls,desc,data=probe(r['pattern'])
    r['dyn']=cls; r['dyn_desc']=desc; r['dyn_data']={str(a):b for a,b in (data or {}).items()}
    r['tested']=True
    if k%20==0: print(k,len(sus)+len(sample),'%.0fs'%(time.time()-t0),flush=True)
json.dump(res,open('analysis.json','w'),default=str)
print('feito')
