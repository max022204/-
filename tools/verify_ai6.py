"""Verify exact AI5-to-AI6 archive changes, original preservation and JASS syntax."""
import hashlib,json,re,subprocess
from pathlib import Path
from mpq import MPQ
from build_continuous import BASE,DEST,function,lobby

checks=[]
def check(name,ok):
    checks.append({'check':name,'passed':bool(ok)});assert ok,name
manifest=json.loads(Path('output/continuous_build_manifest.json').read_text('utf-8'))
base=MPQ(BASE);built=MPQ(DEST)
original=base.read('war3map.j');new=built.read('war3map.j')
check('Packaged script matches tested file',new==Path('output/war3map_ai6.j').read_bytes())
check('Lobby changes only add computer slots 6 and 7',built.read('war3map.w3i')==lobby(base.read('war3map.w3i')))
names=set((base.read('(listfile)') or b'').decode('utf-8',errors='replace').splitlines())
names.update(['war3map.w3e','war3map.wpm','war3map.doo','war3mapUnits.doo','war3map.shd','war3map.w3a','war3map.w3b','war3map.w3d','war3mapMisc.txt'])
names.update('Units\\'+p.name.removeprefix('Units_') for p in Path('extracted').glob('Units_*'))
names.update(m.replace('\\\\','\\') for m in re.findall(r'"([^"\r\n]+\.(?:mdx|mdl|blp|tga|wav|mp3|toc|lua))"',original.decode('latin1'),re.I))
count=0
for name in sorted(names):
    if name in ['war3map.j','war3map.w3i','(listfile)'] or not name:continue
    try:data=base.read(name)
    except UnicodeEncodeError:continue
    if data is not None:
        check('Preserved AI5 resource '+name,built.read(name)==data);count+=1
base.close();built.close()
check('AI5 installed source unchanged',hashlib.sha256(BASE.read_bytes()).hexdigest()==manifest['base_sha256'])
original_path=Path('C:/Program Files (x86)/War3 v1.29c/Maps/000羈絆7.3.7.w3x')
check('User original map unchanged',hashlib.sha256(original_path.read_bytes()).digest()==hashlib.sha256(Path('output/original.w3x').read_bytes()).digest())
check('Output map hash matches manifest',hashlib.sha256(DEST.read_bytes()).hexdigest()==manifest['modified_sha256'])
# Analyze only executable function declarations, not callback text inside other functions.
old=original.decode('latin1').replace('\r\n','\n');s=new.decode('latin1')
new_functions={m[1]:m[0] for m in re.finditer(r'^function (\w+) takes .*?^endfunction',s,re.M|re.S)}
count_functions=0
for m in re.finditer(r'^function (\w+) takes .*?^endfunction',old,re.M|re.S):
    if m[1] not in manifest['changed_functions']:
        check('Unchanged AI5 function '+m[1],new_functions[m[1]]==m[0]);count_functions+=1
check('Every original function retained',len(new_functions)>=count_functions+len(manifest['changed_functions']))
check('Growth no longer gated by wave readiness','CAIReadiness' not in function(s,'CAIGrow') and 'CAIReadiness' not in function(s,'CAIFarmRoom'))
check('Five-computer control cap','n<5' in function(s,'CAIPrepare'))
check('All five default computer controllers',all(f'SetPlayerController(Player({pid}),MAP_CONTROL_COMPUTER)' in s for pid in range(5,10)))
proc=subprocess.run(['tools/pjass.exe','extracted/Scripts_common.j','extracted/Scripts_Blizzard.j','output/war3map_ai6.j'],capture_output=True)
Path('output/ai6_jass_check.txt').write_bytes(proc.stdout+proc.stderr)
check('Full script passes JASS parse/type check',proc.returncode==0)
result=dict(all_passed=True,checks=len(checks),resources_compared=count,preserved_functions=count_functions,runtime_tested=False,details=checks)
Path('output/ai6_verification.json').write_text(json.dumps(result,indent=2),'utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))
