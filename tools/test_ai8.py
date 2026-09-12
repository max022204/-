"""Offline execution of AI8's actual JASS policy with deterministic engine stubs."""
import ast,json,re,hashlib
from pathlib import Path
from build_continuous import function

# Reuse just the translator and engine scaffolding, never run the AI6 test suite.
tree=ast.parse(Path('tools/test_ai6.py').read_text('utf-8'))
scope=dict(re=re,function=function,src=Path('output/war3map_ai8.j').read_text('utf-8',errors='replace'))
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['translate','hero','environment']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<AI6 test helper>','exec'),scope)
names=['CAIPrepare','CAIRoleRank','CAIGrow','CAIWantDefense','CAIAllowGrowth','CAITick','CAI8Matches','CAI8Material','CAI8Safe','CAI8Equipped','CAI8BeachOpen','CAI8StartTrip','CAI8Trip','CAI8Return','CAI8RoleCast']
scope['compiled']='\n\n'.join(re.sub(r'\$([A-Fa-f0-9]+)',r'0x\1',scope['translate'](n)) for n in names)
hero=scope['hero'];results=[]
def check(name,ok):
    results.append(dict(test=name,passed=bool(ok)))
    assert ok,name
def env(**kw):
    e=scope['environment']()
    for name in ['Role','Hero','Assigned','TripKind','Step','Until','Retry','Progress','LastHP','LootUntil']:
        e['CAI8'+name]={i:0 for i in range(10)}
    e['CAI8Target']={i:None for i in range(10)}
    e.update(CAI8CC=None,CAI8CCUntil=0.,CAI8Equipped=lambda h:True,CAI8StartTrip=lambda h:False,
        CAI8BeachOpen=lambda:False,CAISampleDPS={i:1000. for i in range(10)},CAISampleAt={i:99. for i in range(10)},
        CAIWatchSignature={i:'gear' for i in range(10)},CAILoadout=lambda h:'gear',CAIAttack=lambda h:h.get('attack',1.),
        CAIPrimary=lambda h:1,CAI8Material=lambda h:0,CAIHGConditions=lambda h:True)
    e.update(kw)
    return e
def actual(e,name):
    exec(re.sub(r'\$([A-Fa-f0-9]+)',r'0x\1',scope['translate'](name)),e)

e=env(GetPlayerController=lambda p:1 if p>=2 else 0);e['CAIPrepare']()
check('Eight default computer slots; two human slots untouched',[p for p in range(10) if e['CAIActive'][p]]==list(range(2,10)))
check('Two support, two control, clear, two burst and tank',[e['CAI8Role'][e['CAI8Assigned'][p]] for p in range(2,10)]==[1,1,2,2,3,4,4,5])
for pid,id in zip(range(2,10),['H00Q','H046','H00O','E00L','N02F','E020','E06N','E02L']):
    check('Assigned hero '+id,e['CAIRoleRank'](pid,id)==10000)
e=env(GetPlayerController=lambda p:0);e['CAIPrepare']();check('Never take over human players',not any(e['CAIActive'].values()))
e=env(GetPlayerController=lambda p:1);e['CAIPrepare']();check('At most eight bots even with ten computer slots',sum(e['CAIActive'].values())==8)

def grow(h,**kw):
    calls=[];e=env()
    for name,label in [('CAIWater','water'),('CAIGear','gear'),('CAIFarmRoom','room'),('CAIFightMirror','mirror'),('CAI8Trip','trip')]:
        e[name]=lambda h,label=label:calls.append(label) or True
    e['CAIEnterRoom']=lambda h,r:calls.append('gold' if r==2 else 'xp') or True
    e.update(kw);e['CAIGrow'](h);return calls,e
for p in range(2,10):
    check('Level one water opening player '+str(p),grow(hero(p,level=1,gold=0))[0]==['water'])
check('Two genuine deliveries required',grow(hero(),CAIWaterDone={0:1})[0]==['water'])
check('Affordable equipment before trips',grow(hero())[0]==['gear'])
check('Basic gear required before advanced training',grow(hero(cost=300000),CAI8Equipped=lambda h:False)[0]==['gear'])
check('No current-wave power cap on earning',grow(hero(cost=300000,hp=1e9,life=1e9))[0]==['gold'])
check('Active trip continues without shopping interruption',grow(hero(),CAI8TripKind={0:1})[0]==['trip'])

for tier,ids in [(1,['ngno','ngnv','n033','n032']),(2,['n02O']),(3,['n02Y','n02Z']),(4,['n03R','n03S','n03U','n03T','n03V'])]:
    e=env()
    check('Actual native drop/event unit tier '+str(tier),all(e['CAI8Matches'](id,tier) for id in ids))
check('Ogres do not falsely supply tier-two stones',not e['CAI8Matches']('ngnv',2))
e=env();actual(e,'CAI8Material');e.update(CAIRecipeBase='base',CAIRecipeGem='stone',CAIRecipeResult='result',CAIRecipeData=lambda *a:None,CAIOwned=lambda h,id:id=='base')
check('Hunt missing recipe stone',e['CAI8Material'](hero())==1)
e['CAIOwned']=lambda h,id:id in ['base','stone'];check('Do not hunt already-owned stone',e['CAI8Material'](hero())==0)
e=env();h=hero();enemy=hero(12,life=1000.,attack=10.)
check('Safe target requires combat evidence',e['CAI8Safe'](h,enemy))
enemy['attack']=9999999.;check('Reject extreme ogre damage',not e['CAI8Safe'](h,enemy))
enemy['attack']=10.;e['CAISampleAt'][0]=0.;check('Reject stale DPS estimate',not e['CAI8Safe'](h,enemy))
e['CAISampleAt'][0]=99.;e['CAIWatchSignature'][0]='old';check('Reject changed loadout',not e['CAI8Safe'](h,enemy))

for flag in [0,1]:
    e=env(YDHT=0,GetHandleId=lambda p:p,PLAYER_NEUTRAL_PASSIVE=15,LoadInteger=lambda *a:flag);actual(e,'CAI8BeachOpen')
    check('Native beach flag '+str(flag),e['CAI8BeachOpen']()==bool(flag))
calls=[];h=hero();mentor=hero(x=1.,y=2.);dong=hero(x=3.,y=4.)
e=env(CAI8BeachOpen=lambda:True,CAIBuy=lambda h,id,*a:calls.append(id) or True,gg_unit_n00A_0077=mentor,gg_unit_n00R_0010=dong,gg_rct______________031=1,RectContainsUnit=lambda r,h:False)
e['CAI8TripKind'][0]=2;e['CAI8Until'][0]=200.;e['CAI8Trip'](h)
check('Mentor zone voucher first',calls==['I06L'] and e['CAI8Step'][0]==0)
h.update(x=27.6,y=-4359.9);e['CAI8Trip'](h);check('Confirm actual zone teleport',e['CAI8Step'][0]==1)
e['CAI8Trip'](h);check('Dongdong voucher second',calls[-1]=='I0D0' and e['CAI8Step'][0]==1)
e['RectContainsUnit']=lambda *a:True;e['CAI8Trip'](h);check('Confirm actual beach entry',e['CAI8Step'][0]==2)
calls.clear();e['CAI8BeachOpen']=lambda:False;e['CAI8Return']=lambda h:calls.append('return') or True;e['CAI8Trip'](h)
check('Event closure aborts trip',calls==['return'])
calls=[];e=env(CAIRecall=lambda h:False,CAIMoveOrder=lambda *a:calls.append('walk home'),gg_unit_hcas_0007=hero(x=0.,y=0.))
e['CAI8Return'](hero());check('Failed recall walks home instead of idle',calls==['walk home'])

for trigger in ['wave','countdown','enemy']:
    calls=[];hs={i+1:hero(i,x=-5000.) for i in range(10)}
    e=env(CAIActive={i:i>=2 for i in range(10)},udg_Y_Xiong=hs,gg_unit_hcas_0007=hero(x=4000.,y=3500.),
        CAIObserve=lambda:None,CAILearn=lambda h:None,CAIWatchCombat=lambda *a:None,CAISummons=lambda *a:None,
        udg_Dmb_jsq={1:0},TimerGetRemaining=lambda t:8. if trigger=='countdown' else 100.,
        CAIWaveActive=trigger=='wave',CAIFindEnemy=lambda *a:hero(11) if trigger=='enemy' else None,
        CAIRecall=lambda h:calls.append(h['pid']) or True,CAIMoveOrder=lambda *a:None)
    e['CAI8TripKind']={i:2 for i in range(10)};e['CAITick']()
    check('Defense interrupts all eight trips: '+trigger,calls==list(range(2,10)))

# Role casts: execute group scan, skill priority and shared crowd-control lock.
def role_env():
    calls=[];e=env(CreateGroup=lambda:[],GroupEnumUnitsInRange=lambda *a:None,FirstOfGroup=lambda g:None,
        DestroyGroup=lambda g:None,CAICast=lambda h,t,id,*a:calls.append(id) or True)
    return e,calls
for id,spell in [('H00Q','A0JO'),('H046','A0U3'),('H00O','A0B0'),('E00L','A057'),('E02L','A0AR')]:
    e,calls=role_env();e['CAI8RoleCast'](hero(id=id),hero(11))
    check('Role spell '+id,calls==[spell])
e,calls=role_env();t=hero(11);e['CAI8RoleCast'](hero(id='H00O'),t);e['CAI8RoleCast'](hero(id='E00L'),t)
check('Control heroes stagger same-target disables',calls==['A0B0'])
e['CAITime']+=2.;e['CAI8RoleCast'](hero(id='E00L'),t);check('Control lock expires',calls==['A0B0','A057'])
e,calls=role_env();e['CAI8RoleCast'](hero(id='E02L',life=4000.),hero(11));check('Tank survival skill at low health',calls==['A0GJ'])

manifest=json.loads(Path('output/ai8_draft_manifest.json').read_text('utf-8'))
check('Generated script matches manifest',manifest['script_sha256']==hashlib.sha256(Path('output/war3map_ai8.j').read_bytes()).hexdigest())
check('4339 original functions preserved',manifest['preserved_functions']==4339)
Path('output/ai8_policy_tests.json').write_text(json.dumps(dict(passed=len(results),runtime_tested=False,tests=results),indent=2),'utf-8')
print('Passed',len(results),'AI8 offline scenarios; Warcraft engine testing still required.')
