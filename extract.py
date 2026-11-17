import ast, zipfile, os, sys, json, re, glob, sysconfig
FUN={'compile','match','search','fullmatch','sub','subn','findall','finditer','split'}
ALIAS={'re','_re','sre'}
def const_str(n):
    if isinstance(n,ast.Constant) and isinstance(n.value,str): return n.value
    if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):
        a=const_str(n.left); b=const_str(n.right)
        if a is not None and b is not None: return a+b
    return None
def scan(src, origin, out):
    try: tree=ast.parse(src)
    except Exception: return
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in FUN \
           and isinstance(n.func.value,ast.Name) and n.func.value.id in ALIAS and n.args:
            s=const_str(n.args[0])
            if s: out.append((s,origin))
out=[]
# pacotes
for whl in sorted(glob.glob('pkgs/*.whl')):
    pkg=os.path.basename(whl).split('-')[0].lower()
    z=zipfile.ZipFile(whl)
    for name in z.namelist():
        if name.endswith('.py'):
            scan(z.read(name).decode('utf8','ignore'),pkg,out)
# biblioteca padrao
std=sysconfig.get_paths()['stdlib']
for root,dirs,files in os.walk(std):
    if 'site-packages' in root or 'dist-packages' in root or any('test' in p for p in root.split(os.sep)): continue
    for f in files:
        if f.endswith('.py'):
            try: scan(open(os.path.join(root,f),encoding='utf8',errors='ignore').read(),'stdlib',out)
            except Exception: pass
uniq={}
for s,o in out:
    uniq.setdefault(s,set()).add(o)
# manter apenas as que compilam
ok=[]
for s,o in uniq.items():
    try: re.compile(s)
    except Exception: continue
    ok.append({'pattern':s,'origins':sorted(o)})
json.dump(ok,open('corpus.json','w'))
print('chamadas',len(out),'unicas',len(uniq),'compilam',len(ok))
from collections import Counter
c=Counter()
for r in ok:
    for o in r['origins']: c[o]+=1
print(c.most_common())
