import json,re,hashlib,subprocess
from pathlib import Path
from mpq import MPQ
base=MPQ('output/original.w3x');built=MPQ('output/000_Bonds737_AI3.w3x')
checks=[]
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 assert ok,name
check('Repacked JASS exactly matches build input',built.read('war3map.j')==Path('output/war3map_ai.j').read_bytes())
check('Repacked lobby matches build input',built.read('war3map.w3i')==Path('output/war3map_ai.w3i').read_bytes())
names=['war3map.w3e','war3map.wpm','war3map.doo','war3mapUnits.doo','war3map.shd','war3map.w3a','war3map.w3b','war3map.w3d','war3mapMisc.txt','(listfile)']
names += ['Units\\'+p.name.removeprefix('Units_') for p in Path('extracted').glob('Units_*')]
# Verify every resource path actually embedded in the map and referenced by script/object data.
script=Path('extracted/war3map.j').read_bytes().decode('latin1')
names += [m.replace('\\\\','\\') for m in re.findall(r'"([^"\r\n]+\.(?:mdx|mdl|blp|tga|wav|mp3|toc|lua))"',script,re.I)]
for p in Path('extracted').glob('Units_*Strings.txt'):
 names += re.findall(r'(?im)^(?:Art|file|Missileart|Specialart|ResearchArt)=(.+)$',p.read_bytes().decode('latin1'))
n=0
for name in dict.fromkeys(x.strip() for x in names):
 try:
  a=base.read(name)
  if a is not None:check('Unchanged resource: '+name,built.read(name)==a);n+=1
 except UnicodeEncodeError:continue
base.close();built.close()
original=Path('C:/Program Files (x86)/War3 v1.29c/Maps/000羈絆7.3.7.w3x')
check('User original file unchanged',hashlib.sha256(original.read_bytes()).hexdigest()==hashlib.sha256(Path('output/original.w3x').read_bytes()).hexdigest())
check('30 wave unit types extracted',len(json.loads(Path('output/waves.json').read_text('utf-8')))==30)
items=json.loads(Path('output/items.json').read_text('utf-8'))
aisrc=Path('tools/castle_ai.j').read_text('utf-8')+'\n'+Path('tools/growth_ai.j').read_text('utf-8')
for id,gold,lumber in re.findall(r"CAIBuy\(h,'(....)',(\d+),(\d+),",aisrc):
 check('Purchase price matches map: '+id,int(items[id].get('goldcost',0))==int(gold) and int(items[id].get('lumbercost',0))==int(lumber))
check('No flat XP/stat grants in AI source','AddHeroXP(' not in aisrc and 'SetHeroLevel(' not in aisrc and 'SetHeroStr(' not in aisrc)
proc=subprocess.run(['tools/pjass.exe','extracted/Scripts_common.j','extracted/Scripts_Blizzard.j','output/war3map_ai.j'],capture_output=True)
Path('output/jass_check.txt').write_bytes(proc.stdout+proc.stderr)
check('Full JASS parse and type check',proc.returncode==0)
result={'all_passed':True,'checks':len(checks),'resources_compared':n,'runtime_tested':False,'details':checks}
Path('output/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))
