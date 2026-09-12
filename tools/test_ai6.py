"""Execute the actual final AI6 JASS branches with deterministic engine stubs."""
import json,re
from pathlib import Path
from build_continuous import function,patch,lobby
from mpq import MPQ

src=Path('output/war3map_ai6.j').read_text('utf-8',errors='replace')
results=[]
def check(name,ok):
    results.append({'test':name,'passed':bool(ok)});assert ok,name

def translate(name):
    b=function(src,name);m=re.match(r'function \w+ takes (.*?) returns \w+\n(.*)\nendfunction',b,re.S)
    params=[] if m[1]=='nothing' else [p.split()[-1] for p in m[1].split(',')]
    lines=['def '+name+'('+','.join(params)+'):'];indent=1
    globals_=set(re.findall(r'^set (CAI\w+)\s*=',m[2],re.M))
    if globals_:lines.append('    global '+','.join(sorted(globals_)))
    for line in m[2].splitlines():
        l=line.strip()
        if not l or l.startswith('//'):continue
        for a,b in [('true','True'),('false','False'),('null','None')]:l=re.sub(r'\b'+a+r'\b',b,l)
        if l.startswith('local '):
            l=re.sub(r'^local \w+ ','',l)
            if '=' not in l:l+='=None'
        if l.startswith(('set ','call ')):l=l.split(' ',1)[1]
        if l in ['endif','endloop']:indent-=1;continue
        if l=='loop':l='while True:'
        if l.startswith('exitwhen '):l='if '+l[9:]+': break'
        if l.startswith('elseif '):indent-=1;l='elif '+l[7:]
        elif l=='else':indent-=1;l='else:'
        if l.startswith(('if ','elif ')) and not l.endswith(': break'):
            assert l.endswith(' then'),l
            l=l[:-5]+':'
        lines.append('    '*indent+l)
        if l.endswith(':'):
            indent+=1
            lines.append('    '*indent+'pass')
    return '\n'.join(lines)

names=['CAIGrow','CAIWantDefense','CAIAllowGrowth','CAIMoveOrder','CAIAttackOrder',
       'CAIPrepare','CAIRoleRank','CAIMainBoss','CAIFindBoss','CAITick','CAISpells','CAIObserve','CAIFarmRoom']
compiled='\n\n'.join(translate(n) for n in names)
def hero(pid=0,**kw):return dict(dict(pid=pid,x=4000.,y=3500.,hp=10000.,life=10000.,gold=15000,wood=0,level=30,items=set(),id='E020',owner=pid,hero=True),**kw)
def environment(**kw):
    e={'GetOwningPlayer':lambda h:h,'GetPlayerId':lambda h:h['pid'],
       'GetHeroLevel':lambda h:h['level'],'GetUnitX':lambda h:h['x'],'GetUnitY':lambda h:h['y'],
       'GetUnitState':lambda h,s:h['hp'],'GetWidgetLife':lambda h:h['life'],
       'GetPlayerState':lambda h,s:h['wood'] if s==2 else h['gold'],
       'PLAYER_STATE_RESOURCE_GOLD':1,'PLAYER_STATE_RESOURCE_LUMBER':2,'UNIT_STATE_MAX_LIFE':1,
       'CAIHas':lambda h,id:id in h['items'],'CAINear':lambda h,x,y,r:(h['x']-x)**2+(h['y']-y)**2<=r*r,
       'CAIMode':{},'CAITime':100.,'CAIPlannedLumber':0,'CAIWaveActive':False,'CAIHold':False,
       'CAIEquipmentDelivery':lambda h:False,'CAINextGearCost':lambda h:h.get('cost',3000),
       'CAIEnterMirror':lambda h:False,'IMaxBJ':max,'IMinBJ':min,'RMaxBJ':max,'RMinBJ':min,
       'udg_boshu':10,'CAIActive':{i:False for i in range(10)},'CAIBossRole':{i:False for i in range(10)},
       'Player':lambda id:id,'MAP_CONTROL_COMPUTER':1,'PLAYER_SLOT_STATE_PLAYING':1,
       'GetPlayerController':lambda p:1 if p>=5 else 0,'GetPlayerSlotState':lambda p:1,
       'CreateTrigger':lambda:object(),'CAIRank':lambda id:{'H00Q':1000,'H00O':999,'N02F':998}.get(id,100),
       'GetUnitTypeId':lambda h:h['id'],'UNIT_TYPE_HERO':1,'UNIT_TYPE_STRUCTURE':2,
       'IsUnitType':lambda h,t:h.get('hero',False) if t==1 else h.get('structure',False),
       'GetUnitAbilityLevel':lambda h,id:h.get('abilities',{}).get(id,0),
       'OrderId':lambda s:s,'GetUnitCurrentOrder':lambda h:h.get('order','idle'),
       'udg_BOSS_A':{i:'Boss'+str(i) for i in range(1,9)},
       'CAIAlive':lambda h:h is not None and h.get('life',1)>0,
       'IsUnitHidden':lambda h:h.get('hidden',False),
       'R2I':int,'ModuloInteger':lambda a,b:a%b}
    for n,val in [('CAIMirrorSlot',0),('CAIRoom',0),('CAIWaterDone',2),('CAIRoomRetry',0.),('CAIQuiet',5.),
                  ('CAIBusy',0.),('CAIRecover',False),('CAIStuck',0.),('CAILastX',0.),('CAILastY',0.),
                  ('CAIOrderX',0.),('CAIOrderY',0.),('CAIOrderUnit',None),('CAIAttackTarget',None)]:e[n]={i:val for i in range(10)}
    exec(compiled,e);e.update(kw);return e

# Five active computers, exactly three defenders and two specialists; humans untouched.
e=environment();e['CAIPrepare']()
check('Five default computer players controlled',[i for i in range(10) if e['CAIActive'][i]]==[5,6,7,8,9])
check('Original three slots remain defenders',[i for i in range(10) if e['CAIActive'][i] and not e['CAIBossRole'][i]]==[7,8,9])
check('Two added slots have boss roles',[i for i in range(10) if e['CAIBossRole'][i]]==[5,6])
e=environment(GetPlayerController=lambda p:1);e['CAIPrepare']()
check('Even ten configured computers never exceed five controlled bots',sum(e['CAIActive'].values())==5)
check('Custom computer slots still allocate two specialists',sum(e['CAIBossRole'].values())==2)
e=environment(GetPlayerController=lambda p:0);e['CAIPrepare']()
check('Human slots are never controlled',not any(e['CAIActive'].values()))
e=environment();e['CAIBossRole'][5]=True
roster=json.loads(Path('output/ai_ranking.json').read_text('utf-8'))
check('Two strongest role preferences are Kai and Hidan',sorted([r['id'] for r in roster],key=lambda id:e['CAIRoleRank'](5,id),reverse=True)[:2]==['E020','E06N'])
check('Defender preferences unchanged',sorted([r['id'] for r in roster],key=lambda id:e['CAIRoleRank'](7,id),reverse=True)[:3]==['H00Q','H00O','N02F'])
check('Boss selection reserves defender heroes',e['CAIRoleRank'](5,'H00Q')==1)

def policy(h,**kw):
    calls=[];e=environment(**kw)
    for f,label in [('CAIWater','water'),('CAIGear','gear'),('CAIFarmRoom','farm'),('CAIFightMirror','mirror')]:
        e[f]=lambda h,label=label:calls.append(label) or True
    e['CAIEnterRoom']=lambda h,r:calls.append('gold' if r==2 else 'xp') or True
    e['CAIGrow'](h);return calls,e
for stats in [1.,1e8]:
    check('Wave strength never stops saving '+str(stats),policy(hero(hp=stats,life=stats,cost=300000))[0]==['gold'])
check('Affordable equipment precedes training',policy(hero())[0]==['gear'])
check('No available recipe keeps earning for final gear',policy(hero(cost=0))[0]==['gold'])
check('Funded fusion budget keeps training',policy(hero(cost=0,gold=255000))[0]==['xp'])
check('Max level continues earning instead of useless XP',policy(hero(cost=0,gold=255000,level=10000))[0]==['gold'])
check('Insufficient room fee does water',policy(hero(gold=4999))[0]==['water'])
check('Early level does water',policy(hero(level=14,gold=0))[0]==['water'])
for bottle in ['bzbe','bzbf']:check('Finish bottle '+bottle,policy(hero(items={bottle}))[0]==['water'])
check('Two opening deliveries retained',policy(hero(),CAIWaterDone={0:0})[0]==['water'])
check('Revived outside room clears stale assignment',policy(hero(),CAIRoom={0:1})[1]['CAIRoom'][0]==0)
check('Actual room occupant continues farming',policy(hero(x=1545.6,y=4344.2),CAIRoom={0:1})[0]==['farm'])
check('Active mirror fight continues',policy(hero(),CAIMirrorSlot={0:1})[0]==['mirror'])
check('Crafted equipment delivery is retained',policy(hero(),CAIEquipmentDelivery=lambda h:True)[0]==[])
check('Equipment lumber gate retained',policy(hero(),CAIPlannedLumber=5)[0]==['gold'])

def tick(**kw):
    hs={i+1:hero(i) for i in range(5)};base=hero(99)
    calls=[]
    args=dict(udg_Y_Xiong=hs,gg_unit_hcas_0007=base,
        CAIActive={i:i<5 for i in range(10)},udg_Dmb_jsq={1:0},
        TimerGetRemaining=lambda t:100.,CAIObserve=lambda:None,CAILearn=lambda h:None,
        CAIFindEnemy=lambda *a:None,CAIFindBoss=lambda *a:None,CAIWatchCombat=lambda *a:None,
        CAISummons=lambda *a:None,CAISpells=lambda *a:False,
        CAIGrow=lambda h:calls.append(('grow',h['pid'])) or True,
        CAIRecall=lambda h:calls.append(('recall',h['pid'])) or True,
        CAIMoveOrder=lambda *a:None,CAIAttackOrder=lambda h,t:calls.append(('attack',h['pid'])),
        CAIMirrorStarted={i:0. for i in range(5)},udg_Jin_dw={},
        CAIDamageTrigger={i:None for i in range(5)},CAIWatchTarget={},CAISampleDPS={})
    args.update(kw);e=environment(**args)
    return e,hs,calls
e,hs,calls=tick();e['CAITick']();check('All five grow after later waves clear',calls==[('grow',i) for i in range(5)])
for name,kw in [('wave',{'CAIWaveActive':True}),('countdown',{'TimerGetRemaining':lambda t:8.}),('local enemy',{'CAIFindEnemy':lambda *a:hero(11)})]:
    e,hs,calls=tick(**kw)
    for h in hs.values():h['x']=-5000.
    e['CAITick']();check(name+' recalls all five',calls==[('recall',i) for i in range(5)])
e,hs,calls=tick(CAIHold=True);e['CAITick']();check('Hold suppresses all growth',not calls)
e,hs,calls=tick();e['gg_unit_hcas_0007']['life']=500.;e['CAITick']();check('Damaged clear castle does not cause permanent idle',len(calls)==5)
e,hs,calls=tick();e['CAIQuiet']={i:0. for i in range(5)};e['CAITick']();check('Clear debounce prevents instant departure',not calls)
e,hs,calls=tick(CAIWaveActive=True,CAIFindEnemy=lambda *a:hero(11))
hs[1]['x']=6000.;e['CAITick']();check('Fighting a nearby boss does not rubber-band to castle',('recall',0) not in calls and ('attack',0) in calls)

for id,basic in [('E020','A0FB'),('E06N','A0R5')]:
    calls=[];e=environment(CAICast=lambda h,t,id,*a:calls.append(id) or True)
    e['CAIBossRole'][0]=True;h=hero(id=id);target=hero(11,hero=False,id='creep')
    e['CAISpells'](h,target);check(id+' saves burst on ordinary creeps',calls==[basic])
    calls.clear();target['hero']=True;e['CAISpells'](h,target)
    check(id+' opens boss burst with self buff',calls==(['A0HI'] if id=='E020' else ['A109']))

for room in [1,2]:
    calls=[];e=environment(CAIRoom={0:room},CAIRoomUntil={0:190.},CAIRoomStarted={0:0.},
        CAINextGearCost=lambda h:300000,CAIRecall=lambda h:calls.append('recall') or True,
        CAIRoomEnemy=lambda *a:None,CAIMoveOrder=lambda *a:calls.append('farm'))
    e['CAIFarmRoom'](hero(hp=1e9,life=1e9))
    check('Above-wave stats never end room '+str(room),calls==['farm'])

# Actual group traversal verifies invulnerable/staged units and boss priority.
def group_env(units):
    e=environment(CreateGroup=lambda:[],GroupEnumUnitsInRange=lambda g,*a:g.extend(units),
        GroupEnumUnitsOfPlayer=lambda g,*a:g.extend(units),FirstOfGroup=lambda g:g[0] if g else None,
        GroupRemoveUnit=lambda g,u:g.remove(u),DestroyGroup=lambda g:None,
        GetOwningPlayer=lambda h:h['owner'],IsUnitEnemy=lambda u,p:u['owner']!=p,
        CAIWaveForecast=lambda w:None,CAISeenHP={10:0.},CAISeenAttack={10:0.},CAISeenArmor={10:0.},
        udg_guai={10:'creep'},CAIAttack=lambda h:1.,CAIArmor=lambda h:0.)
    return e
for kind in ['invulnerable','hidden','dead','structure']:
    u=hero(11,owner=11)
    if kind=='invulnerable':u['abilities']={'Avul':1}
    if kind=='hidden':u['hidden']=True
    if kind=='dead':u['life']=0.
    if kind=='structure':u['structure']=True
    e=group_env([u]);e['CAIObserve']();check(kind+' enemy never locks growth',not e['CAIWaveActive'])
u=hero(11,owner=11);e=group_env([u]);e['CAIObserve']();check('Live attack unit still interrupts growth',e['CAIWaveActive'])
boss=hero(11,owner=11,id='Boss1',x=5000.);minor=hero(11,owner=11,id='minor',x=4100.)
e=group_env([minor,boss]);check('Main boss prioritized over nearer minor boss',e['CAIFindBoss'](hero(),4000.,3500.) is boss)
boss['abilities']={'Avul':1};e=group_env([boss,minor]);check('Invulnerable boss skipped',e['CAIFindBoss'](hero(),4000.,3500.) is minor)

orders=[];h=hero();enemy=hero(11)
def attack(h,order,t):orders.append(order);h['order']=order
e=environment(IssueTargetOrder=attack);e['CAIAttackOrder'](h,enemy);e['CAIAttackOrder'](h,enemy)
check('Same active attack not restarted',orders==['attack'])
h['order']='idle';e['CAIAttackOrder'](h,enemy);check('Interrupted attack restarts',orders==['attack','attack'])
orders=[];h=hero();pet=hero(id='pet',order='move')
def move(h,order,x,y):orders.append(h['id']);h['order']=order
e=environment(IssuePointOrder=move)
e['CAIMoveOrder'](h,'move',100.,100.);e['CAIMoveOrder'](h,'move',100.,100.)
check('Identical active movement not restarted',orders==['E020'])
e['CAIMoveOrder'](pet,'move',100.,100.)
check('Pet movement not suppressed by hero order cache',orders==['E020','pet'])

Path('output/ai6_policy_tests.json').write_text(json.dumps({'passed':len(results),'engine_tested':False,'tests':results},indent=2),'utf-8')
print('Passed',len(results),'AI6 five-player regression scenarios.')
