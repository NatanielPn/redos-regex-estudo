import json,time
exec(open('exp.py').read().split('# ---------- Experimento ----------')[0].replace("import re, time, json, statistics, sys, multiprocessing as mp","import re, time, json, statistics, sys, multiprocessing as mp"))
rows=[]
for k in range(2,15):
    pat='(a|b)*a'+'(a|b)'*(k-1)
    N=compile_nfa(pat)
    t=time.perf_counter(); D=build_dfa(N,['a','b']); dt=time.perf_counter()-t
    # sanity vs re
    import re as _re
    for w in ['a'+'b'*(k-1),'b'+'a'*(k-1),'ab'*k,'b'*k]:
        assert dfa_match(D,w)==bool(_re.fullmatch(pat,w)),(k,w)
    # nfa simulation time on a 10000-char input
    text=('ab'*5000)
    t0=time.perf_counter(); nfa_match(N,text); tn=time.perf_counter()-t0
    rows.append({'k':k,'pattern_len':len(pat),'nfa':len(N.eps),'dfa':len(D[0]),'dfa_build_s':dt,'nfa_10000_s':tn})
    print(rows[-1],flush=True)
json.dump(rows,open('results2.json','w'),indent=1)
