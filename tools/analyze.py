import re,json
from pathlib import Path
OUT=Path('output'); OUT.mkdir(exist_ok=True)
def slk(p):
 rows={};x=y=1
 for line in p.read_text('utf-8-sig',errors='replace').splitlines():
  if not line.startswith('C;'):continue
  m=re.search(r'(?:^|;)X(\d+)',line)
  if m:x=int(m[1])
  m=re.search(r'(?:^|;)Y(\d+)',line)
  if m:y=int(m[1])
  m=re.search(r'(?:^|;)K(.*)$',line)
  if m:
   v=m[1];v=v[1:-1].replace('""','"') if v.startswith('"') else v
   rows.setdefault(y,{})[x]=v
 headers=rows.pop(1)
 return {r[1]:{headers[k]:v for k,v in r.items() if k in headers} for r in rows.values() if 1 in r}
def txt(p):
 data={};cur=None
 for l in p.read_text('utf-8-sig',errors='replace').splitlines():
  if re.fullmatch(r'\[.+\]',l):cur=data.setdefault(l[1:-1],{})
  elif cur is not None and '=' in l:
   k,v=l.split('=',1);cur[k]=v
 return data
tables={p.stem.removeprefix('Units_'):slk(p) for p in Path('extracted').glob('*.slk')}
units={}; abilities={};items={}
for key in ['UnitData','UnitBalance','UnitAbilities','UnitUI','UnitWeapons']:
 for id,v in tables[key].items():units.setdefault(id,{}).update(v)
for p in Path('extracted').glob('*UnitStrings.txt'):
 for id,v in txt(p).items():units.setdefault(id,{}).update(v)
abilities=tables['AbilityData']
for p in Path('extracted').glob('*AbilityStrings.txt'):
 for id,v in txt(p).items():abilities.setdefault(id,{}).update(v)
items=tables['ItemData']
for id,v in txt(Path('extracted/Units_ItemStrings.txt')).items():items.setdefault(id,{}).update(v)
j=Path('extracted/war3map.j').read_text('utf-8-sig',errors='replace')
def raw(h):return bytes.fromhex(h).decode('latin1')
waves={int(n):raw(h) for n,h in re.findall(r'set udg_guai\[(\d+)\]=\$([0-9A-F]{8})',j)}
placed=[]
for m in re.finditer(r'set u=CreateUnit\(Player\((\d+)\),\$([0-9A-F]{8}),([\d.-]+),([\d.-]+),([\d.-]+)\)(.*?)(?=set u=CreateUnit|endfunction)',j,re.S):
 owner,h,x,y,face,tail=m.groups();id=raw(h)
 var=re.search(r'set (gg_unit_\w+)=u',tail)
 if id[0].isupper() and owner=='15' and float(x)>3900 and float(y)>3900:
  placed.append({'variable':var[1] if var else '', 'id':id,'x':float(x),'y':float(y),'name':units.get(id,{}).get('Propernames',''),'unit':units.get(id,{})})
for name,obj in [('units',units),('abilities',abilities),('items',items),('waves',waves),('placed_heroes',placed)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
print('units',len(units),'abilities',len(abilities),'items',len(items),'waves',waves)
for p in placed:print(p['variable'],p['name'])
