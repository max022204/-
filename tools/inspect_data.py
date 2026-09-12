import json,re,sys
from pathlib import Path
u=json.loads(Path('output/units.json').read_text('utf-8'));a=json.loads(Path('output/abilities.json').read_text('utf-8'));it=json.loads(Path('output/items.json').read_text('utf-8'))
def clean(s):return re.sub(r'\|c[0-9a-fA-F]{8}|\|r','',s).replace('|n',' ')
for p in json.loads(Path('output/placed_heroes.json').read_text('utf-8')):
 v=p['unit'];print('\n',p['id'],p['name'],'stats',*[v.get(k,'') for k in ['STR','STRplus','AGI','AGIplus','INT','INTplus','Primary','HP','def','rangeN1','cool1']])
 for aid in v.get('heroAbilList','').split(','):
  av=a.get(aid,{})
  print(aid,av.get('code'),av.get('Order'),clean(av.get('Name','')),clean(av.get('Researchubertip',av.get('Ubertip','')))[:1500])
Path('output/upgrades.json').write_text(json.dumps(__import__('analyze').tables['UpgradeData'],ensure_ascii=False,indent=2),'utf-8')
