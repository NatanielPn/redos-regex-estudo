import re, time, json, statistics, sys, multiprocessing as mp
exec(open('exp.py').read().split('# ---------- Experimento ----------')[0])
REPS=5; TIMEOUT=3.0
def st(v):
    raw=list(v); v=sorted(v); return {'med':statistics.median(v),'min':v[0],'max':v[-1],'mean':statistics.mean(v),'sd':(statistics.stdev(v) if len(v)>1 else 0.0),'raw':raw}
CASES=[('P1','(a+)+'),('P2','(a|aa)+'),('P3','(a*)*'),('P4','(a|a)*'),('C1','a*b')]
out={'python':sys.version.split()[0],'reps':REPS,'timeout':TIMEOUT,'cases':[]}
for name,pat in CASES:
    N=compile_nfa(pat); D=build_dfa(N,['a','b'])
    rec={'name':name,'pattern':pat,'nfa_states':len(N.eps),'dfa_states':len(D[0]),'rows':[]}
    bt_run(pat,'a'*12+'b',TIMEOUT)  # aquecimento
    stop=False
    for n in list(range(4,31,2))+[50,100,1000,10000]:
        text='a'*n+'b'; row={'n':n}
        if not stop:
            ts=[];to=0
            for k in range(REPS):
                t,r=bt_run(pat,text,TIMEOUT)
                if t is None:
                    to+=1
                    if to>=2 and len(ts)<=to: break   # maioria estourou
                else: ts.append(t)
            row['bt']={'timeouts':to,'trials':len(ts)+to,**(st(ts) if ts else {})}
            if to>=(len(ts)+to+1)//2 : stop=True
        else: row['bt']={'timeouts':REPS,'trials':0}
        for nm,f in (('nfa',lambda:nfa_match(N,text)),('dfa',lambda:dfa_match(D,text))):
            f(); ts=[]
            for k in range(REPS):
                t=time.perf_counter(); r=f(); ts.append(time.perf_counter()-t)
            row[nm]=st(ts)
        rec['rows'].append(row)
    out['cases'].append(rec); print('done',name,flush=True)
json.dump(out,open('results6.json','w'),indent=1)
# L_k com repeticoes
import re as _re
rows=[]
for k in range(2,15):
    pat='(a|b)*a'+'(a|b)'*(k-1); N=compile_nfa(pat)
    bs=[]
    for _ in range(REPS):
        t=time.perf_counter(); D=build_dfa(N,['a','b']); bs.append(time.perf_counter()-t)
    for w in ['a'+'b'*(k-1),'b'+'a'*(k-1),'ab'*k,'b'*k]:
        assert dfa_match(D,w)==bool(_re.fullmatch(pat,w))
    text='ab'*5000; ns=[]
    for _ in range(REPS):
        t0=time.perf_counter(); nfa_match(N,text); ns.append(time.perf_counter()-t0)
    rows.append({'k':k,'nfa':len(N.eps),'dfa':len(D[0]),'build':st(bs),'nfa10000':st(ns)})
json.dump(rows,open('results7.json','w'),indent=1)
print('fim')
