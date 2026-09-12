"""Execute the actual straight-line JASS policy functions with deterministic game stubs.
This tests policy branches, not the Warcraft engine or native-extension implementation.
"""
import re,json
from pathlib import Path
source=Path('tools/growth_ai.j').read_text('utf-8')+'\n'+Path('tools/castle_ai.j').read_text('utf-8')
def translate(name):
 m=re.search(r'function '+name+r' takes (.*?) returns \w+\n(.*?)\nendfunction',source,re.S)
 params=[] if m[1]=='nothing' else [p.split()[-1] for p in m[1].split(',')]
 lines=['def '+name+'('+','.join(params)+'):']
 assigned=set(re.findall(r'^set (CAI\w+)\s*=',m[2],re.M))
 if assigned:lines.append('    global '+','.join(sorted(assigned)))
 indent=1
 for l in m[2].splitlines():
  l=l.strip()
  if not l or l.startswith('//'):continue
  l=re.sub(r'\btrue\b','True',l);l=re.sub(r'\bfalse\b','False',l);l=re.sub(r'\bnull\b','None',l)
  if l.startswith('local '):
   l=re.sub(r'^local \w+ ','',l)
   if '=' not in l:l+='=None'
  if l.startswith(('set ','call ')):l=l.split(' ',1)[1]
  if l=='endif':indent-=1;continue
  if l.startswith('elseif '):indent-=1;l='elif '+l[7:]
  elif l=='else':indent-=1;l='else:'
  if l.startswith(('if ','elif ')):assert l.endswith(' then');l=l[:-5]+':'
  lines.append('    '*indent+l)
  if l.endswith(':'):indent+=1
 return '\n'.join(lines)
functions=['CAIReadiness','CAIGrow','CAIEnterRoom','CAIWater']
compiled='\n\n'.join(translate(n) for n in functions)
Path('output/growth_policy_test_translation.py').write_text(compiled,'utf-8')
results=[]
def env(**kwargs):
 e={'CAIFactor':2.5,'CAITargetHP':1000.,'CAITargetAttack':100.,'CAITargetArmor':10.,'CAITargetWave':1,'CAITime':100.,'UNIT_STATE_MAX_LIFE':1,'PLAYER_STATE_RESOURCE_GOLD':1,
 'CAIRoom':{0:0},'CAIRoomStarted':{},'CAIRoomUntil':{},'CAIRoomRetry':{0:0.},'CAIMode':{},'CAIWaterDone':{0:2},'gg_unit_n00A_0077':{'x':3968.,'y':3520.},
 'GetUnitState':lambda h,s:h['hp'],'CAIAttack':lambda h:h['attack'],'CAIArmor':lambda h:h['armor'],
 'GetOwningPlayer':lambda h:h,'GetPlayerId':lambda h:0,'GetPlayerState':lambda h,s:h['gold'],'GetHeroLevel':lambda h:h['level'],
 'CAIHas':lambda h,id:id in h.get('items',set()),'UnitInventoryCount':lambda h:len(h.get('items',set())),
 'CAINextGearCost':lambda h:h.get('cost',3000),'IMaxBJ':max,'RMaxBJ':max,'RMinBJ':min,
 'GetUnitX':lambda h:h['x'],'GetUnitY':lambda h:h['y'],
 'CAINear':lambda h,x,y,r:(h.get('x',0)-x)**2+(h.get('y',0)-y)**2<=r*r,
 'IssuePointOrder':lambda *args:True}
 e.update(kwargs);exec(compiled,e);return e
def hero(**kw):return dict({'hp':400.,'attack':40.,'armor':4.,'gold':15000,'level':30,'items':set(),'x':3968.,'y':3520.,'cost':3000},**kw)
def check(name,ok):
 results.append({'test':name,'passed':bool(ok)});assert ok,name
e=env();h=hero()
check('Exact 2.5x threshold qualifies',e['CAIReadiness'](h)==1.)
for stat,value in [('hp',399),('attack',39.9),('armor',3.9)]:
 x=h|{stat:value};check('Each component independently required: '+stat,e['CAIReadiness'](x)<1.)
e['CAITargetArmor']=0.;check('Zero enemy armor imposes no extra requirement',e['CAIReadiness'](h|{'armor':0})==1.)
for factor in [2.,3.]:
 e['CAIFactor']=factor;check('Multiplier is on AI, not enemy: '+str(factor),abs(e['CAIReadiness'](h)-factor*.4)<1e-8)
def policy(h,deliveries=2,room=0):
 calls=[];e=env();e['CAIWaterDone'][0]=deliveries;e['CAIRoom'][0]=room
 e['CAIWater']=lambda h:calls.append('water') or True
 e['CAIGear']=lambda h:calls.append('gear') or True
 e['CAIEnterRoom']=lambda h,r:calls.append('xp' if r==1 else 'gold') or True
 e['CAIFarmRoom']=lambda h:calls.append('farm') or True
 e['CAIGrow'](h);return calls,e
for count in [0,1]:check('Opening delivery '+str(count)+' precedes shopping',policy(hero(),count)[0]==['water'])
check('Full bottle submitted before spending',policy(hero()|{'items':{'bzbf'}})[0]==['water'])
check('Empty bottle trip continues before spending',policy(hero()|{'items':{'bzbe'}})[0]==['water'])
check('Level 14 cannot enter rooms',policy(hero()|{'level':14,'gold':0})[0]==['water'])
check('Level deficit routes to XP room',policy(hero()|{'level':15,'attack':1})[0]==['xp'])
check('Funds deficit routes to gold room',policy(hero()|{'gold':5000,'attack':1})[0]==['gold'])
check('Affordable gear preserves 5000 room reserve',policy(hero())[0]==['gear'])
check('Insufficient entry money returns to water',policy(hero()|{'gold':4999,'attack':1})[0]==['water'])
check('Already in room continues session',policy(hero(),room=1)[0]==['farm'])
check('Reached target with no next gear returns to guard',policy(hero()|{'cost':0})[0]==[])
for level,gold in [(14,5000),(15,4999)]:
 e=env();e['CAIBuy']=lambda *args:(_ for _ in ()).throw(AssertionError('Must not spend'))
 check('Room gate level/money '+str((level,gold)),e['CAIEnterRoom'](hero()|{'level':level,'gold':gold},1)==False)
e=env();e['CAIBuy']=lambda *args:True;h=hero()
e['CAIEnterRoom'](h,1)
check('Failed teleport never marks hero as inside room',e['CAIRoom'][0]==0)
check('Failed teleport backs off before retry',e['CAIRoomRetry'][0]==115.)
e=env();h=hero()
def teleport(h,*args):h['x']=1545.6;h['y']=4344.2;return True
e['CAIBuy']=teleport;e['CAIEnterRoom'](h,1)
check('Verified teleport starts bounded training session',e['CAIRoom'][0]==1 and e['CAIRoomUntil'][0]==160.)
e=env();h=hero()|{'items':{'bzbf'}}
e['CAIBuy']=lambda h,*args:h['items'].discard('bzbf') or True
e['CAIWater'](h);check('Delivery counter advances only after bottle consumed',e['CAIWaterDone'][0]==3)
e=env();e['CAIBuy']=lambda *args:True;e['CAIWater'](hero()|{'items':{'bzbf'}})
check('Movement toward NPC is not a completed delivery',e['CAIWaterDone'][0]==2)
Path('output/growth_policy_tests.json').write_text(json.dumps({'passed':len(results),'engine_tested':False,'tests':results},indent=2),'utf-8')
print('Passed',len(results),'policy tests (actual translated JASS policy functions).')
