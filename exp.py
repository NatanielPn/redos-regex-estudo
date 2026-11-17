import re, time, json, statistics, sys, multiprocessing as mp
sys.setrecursionlimit(10000)

# ---------- Mini regex -> NFA (Thompson), subset construction -> DFA ----------
# AST parser for: literals, '.', '|', '*', '+', '?', groups ( ). Anchored full match.
class P:
    def __init__(s, t): s.t=t; s.i=0
    def peek(s): return s.t[s.i] if s.i<len(s.t) else None
    def eat(s): c=s.t[s.i]; s.i+=1; return c
    def alt(s):
        n=s.cat()
        while s.peek()=='|':
            s.eat(); n=('alt',n,s.cat())
        return n
    def cat(s):
        n=None
        while s.peek() not in (None,'|',')'):
            r=s.rep()
            n=r if n is None else ('cat',n,r)
        return n if n is not None else ('eps',)
    def rep(s):
        n=s.atom()
        while s.peek() in ('*','+','?'):
            o=s.eat()
            n=({'*':'star','+':'plus','?':'opt'}[o],n)
        return n
    def atom(s):
        c=s.eat()
        if c=='(':
            n=s.alt(); assert s.eat()==')'; return n
        if c=='.': return ('any',)
        return ('lit',c)

class NFA:
    def __init__(s): s.eps=[]; s.tr=[]  # tr[state]=list of (label,target); label None=eps handled in eps
    def new(s): s.eps.append([]); s.tr.append([]); return len(s.eps)-1

def build(n, N):
    t=n[0]
    if t=='lit' or t=='any':
        a=N.new(); b=N.new(); N.tr[a].append((n[1] if t=='lit' else '.', b)); return a,b
    if t=='eps':
        a=N.new(); b=N.new(); N.eps[a].append(b); return a,b
    if t=='cat':
        a1,b1=build(n[1],N); a2,b2=build(n[2],N); N.eps[b1].append(a2); return a1,b2
    if t=='alt':
        a=N.new(); b=N.new(); a1,b1=build(n[1],N); a2,b2=build(n[2],N)
        N.eps[a]+= [a1,a2]; N.eps[b1].append(b); N.eps[b2].append(b); return a,b
    if t in ('star','plus','opt'):
        a=N.new(); b=N.new(); a1,b1=build(n[1],N)
        N.eps[a].append(a1); N.eps[b1].append(b)
        if t in ('star','plus'): N.eps[b1].append(a1)
        if t in ('star','opt'): N.eps[a].append(b)
        return a,b

def compile_nfa(pat):
    ast=P(pat).alt(); N=NFA(); s,f=build(ast,N); N.s=s; N.f=f; return N

def closure(N, S):
    st=list(S); seen=set(S)
    while st:
        x=st.pop()
        for y in N.eps[x]:
            if y not in seen: seen.add(y); st.append(y)
    return frozenset(seen)

def step(N, S, ch):
    out=set()
    for x in S:
        for lab,y in N.tr[x]:
            if lab=='.' or lab==ch: out.add(y)
    return closure(N,out)

def nfa_match(N, text):   # simulacao em O(m*n)
    S=closure(N,{N.s})
    for ch in text:
        S=step(N,S,ch)
        if not S: return False
    return N.f in S

def build_dfa(N, alphabet):
    start=closure(N,{N.s}); ids={start:0}; trans=[{}]; acc=[N.f in start]; work=[start]
    while work:
        S=work.pop(); i=ids[S]
        for ch in alphabet:
            T=step(N,S,ch)
            if T not in ids:
                ids[T]=len(ids); trans.append({}); acc.append(N.f in T); work.append(T)
            trans[i][ch]=ids[T]
    return trans,acc

def dfa_match(D, text):
    trans,acc=D; q=0
    for ch in text:
        q=trans[q].get(ch)
        if q is None: return False
    return acc[q]

def timeit(f, reps=3):
    best=1e18; r=None
    for _ in range(reps):
        t=time.perf_counter(); r=f(); d=time.perf_counter()-t
        best=min(best,d)
    return best,r

def _bt_worker(pat,text,q):
    r=re.compile('^(?:'+pat+')$')
    t=time.perf_counter(); m=r.match(text); d=time.perf_counter()-t
    q.put((d,bool(m)))

def bt_run(pat,text,limit):
    q=mp.Queue(); p=mp.Process(target=_bt_worker,args=(pat,text,q)); p.start()
    p.join(limit)
    if p.is_alive():
        p.terminate(); p.join(); return None,None
    return q.get()

# ---------- Experimento ----------
CASES=[
 ('P1 (a+)+',    '(a+)+',       lambda n:'a'*n+'b'),
 ('P2 (a|aa)+',  '(a|aa)+',     lambda n:'a'*n+'b'),
 ('P3 (a*)*',    '(a*)*',       lambda n:'a'*n+'b'),
 ('P4 (a|a)*',   '(a|a)*',      lambda n:'a'*n+'b'),
 ('C1 a*b (controle)', 'a*b',   lambda n:'a'*n+'b'),
]
TIMEOUT=3.0
out={'python':sys.version.split()[0],'cases':[]}
for name,pat,gen in CASES:
    N=compile_nfa(pat)
    tb=time.perf_counter(); D=build_dfa(N,['a','b']); tdfa=time.perf_counter()-tb
    rec={'name':name,'pattern':pat,'nfa_states':len(N.eps),'dfa_states':len(D[0]),'dfa_build_s':tdfa,'rows':[]}
    py=re.compile('^(?:'+pat+')$')
    n=4; stop_bt=False
    sizes=list(range(4,31,2))+[50,100,1000,10000]
    for n in sizes:
        text=gen(n)
        row={'n':n}
        if not stop_bt:
            t,r=bt_run(pat,text,TIMEOUT)
            if t is None: stop_bt=True; row['bt_s']=None
            else: row['bt_s']=t; row['bt_res']=r
        else:
            row['bt_s']=None
        t,r=timeit(lambda: nfa_match(N,text)); row['nfa_s']=t; row['nfa_res']=bool(r)
        t,r=timeit(lambda: dfa_match(D,text)); row['dfa_s']=t; row['dfa_res']=bool(r)
        # coerencia
        ref=row['bt_res'] if row['bt_s'] is not None else row['nfa_res']
        assert row['nfa_res']==row['dfa_res']==ref,(name,n)
        rec['rows'].append(row)
    out['cases'].append(rec); print('done',name,flush=True)
json.dump(out,open('results.json','w'),indent=1)
for c in out['cases']:
    print(c['name'],'NFA',c['nfa_states'],'DFA',c['dfa_states'],'build %.4fs'%c['dfa_build_s'])
    for r in c['rows']:
        print('  n=%-6d bt=%s nfa=%.6f dfa=%.6f'%(r['n'],('%.4f'%r['bt_s']) if r['bt_s'] is not None else 'timeout',r['nfa_s'],r['dfa_s']))
