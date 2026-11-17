import re, time, json, statistics, sys, multiprocessing as mp
src=open('exp.py').read().split('# ---------- Experimento ----------')[0]
exec(src)
sys.setrecursionlimit(100000)
REPS=7
def stats(v): 
    v=sorted(v); return {'med':statistics.median(v),'min':v[0],'max':v[-1],'n':len(v)}
# ---- backtracking de referencia em Python puro sobre o AFN de Thompson (sem memoizacao)
def bt_nfa(N,text):
    L=len(text)
    def go(s,i,seen):
        if s==N.f and i==L: return True
        for y in N.eps[s]:
            if y not in seen:
                if go(y,i,seen|{s} if False else seen|{y}): return True
        if i<L:
            for lab,y in N.tr[s]:
                if lab=='.' or lab==text[i]:
                    if go(y,i+1,frozenset({y})): return True
        return False
    return go(N.s,0,frozenset({N.s}))
def _w(fn,pat,text,q):
    if fn=='re':
        r=re.compile('^(?:'+pat+')$'); t=time.perf_counter(); m=r.match(text)
    else:
        N=compile_nfa(pat); t=time.perf_counter(); m=bt_nfa(N,text)
    q.put((time.perf_counter()-t,bool(m)))
def run(fn,pat,text,limit):
    q=mp.Queue(); p=mp.Process(target=_w,args=(fn,pat,text,q)); p.start(); p.join(limit)
    if p.is_alive(): p.terminate(); p.join(); return None
    return q.get()[0]
PATS=[('P1','(a+)+'),('P2','(a|aa)+'),('P3','(a*)*'),('P4','(a|a)*'),('C1','a*b')]
out={'python':sys.version.split()[0],'reps':REPS,'A':{}, 'B':{}}
# A: protocolo com repeticoes
for name,pat in PATS:
    N=compile_nfa(pat); D=build_dfa(N,['a','b']); rec={}
    run('re',pat,'a'*12+'b',3.0)  # aquecimento
    for n in (16,20,24,26,28,30):
        ts=[];to=0
        for k in range(REPS):
            t=run('re',pat,'a'*n+'b',3.0)
            if t is None: to+=1
            else: ts.append(t)
            if to>=2 and k>=1: break
        rec[n]={'timeouts':to,'trials':len(ts)+to,**(stats(ts) if ts else {})}
    for n in (1000,10000):
        text='a'*n+'b'
        for nm,f in (('nfa',lambda:nfa_match(N,text)),('dfa',lambda:dfa_match(D,text))):
            ts=[]
            for k in range(REPS):
                t=time.perf_counter(); f(); ts.append(time.perf_counter()-t)
            rec[f'{nm}{n}']=stats(ts)
    out['A'][name]=rec; print('A',name,flush=True)
# B: backtracking em Python puro x simulacao do AFN em Python puro
for name,pat in PATS[:4]:
    N=compile_nfa(pat); rec={}
    for n in (10,12,14,16,18,20,22,24):
        ts=[]
        for k in range(3):
            t=run('py',pat,'a'*n+'b',8.0)
            if t is None: ts=None;break
            ts.append(t)
        sim=[]
        for k in range(7):
            t=time.perf_counter(); nfa_match(N,'a'*n+'b'); sim.append(time.perf_counter()-t)
        rec[n]={'bt_py':(statistics.median(ts) if ts else None),'nfa_py':statistics.median(sim)}
        if ts is None: break
    out['B'][name]=rec; print('B',name,flush=True)
json.dump(out,open('results3.json','w'))
