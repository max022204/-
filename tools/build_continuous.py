"""Patch the user's installed AI5 without replacing its equipment/mirror systems."""
import argparse,ctypes as c,hashlib,json,re,shutil,struct
from pathlib import Path
from mpq import MPQ

BASE=Path('C:/Program Files (x86)/War3 v1.29c/Maps/000_Bonds737_AI5.w3x')
DEST=Path('output/000_Bonds737_AI6.w3x')

def function(source,name):
    matches=list(re.finditer(r'^function '+name+r' takes .*?^endfunction',source,re.M|re.S))
    assert len(matches)==1,(name,len(matches))
    return matches[0][0]

def patch(source):
    source=source.replace('\r\n','\n')
    original=source
    updated=[]
    def update(name,body):
        nonlocal source
        old=function(source,name)
        assert old!=body,name+' unchanged'
        source=source.replace(old,body,1);updated.append(name)
    additions=Path('tools/continuous_ai.j').read_text('utf-8')
    grow=function(additions,'CAIGrow')
    helper=additions.replace(grow,'')
    assert 'real array CAIOrderX' not in source,'AI6 already applied'
    source=source.replace('endglobals','boolean array CAIBossRole\nunit array CAIOrderUnit\nreal array CAIOrderX\nreal array CAIOrderY\nunit array CAIAttackTarget\nreal array CAILastX\nreal array CAILastY\nreal array CAIStuck\nendglobals',1)
    source=source.replace('function CAIFindEnemy takes',helper+'\nfunction CAIFindEnemy takes',1)
    source=source.replace('function CAICast takes',Path('tools/boss_ai.j').read_text('utf-8')+'\nfunction CAICast takes',1)
    update('CAIPrepare','''function CAIPrepare takes nothing returns nothing
local integer i=7
local integer n=0
set CAISelectionContext=CreateTrigger()
// Preserve the original three defender slots before assigning additional bots.
loop
exitwhen i>=10
if GetPlayerController(Player(i))==MAP_CONTROL_COMPUTER and GetPlayerSlotState(Player(i))==PLAYER_SLOT_STATE_PLAYING then
set CAIActive[i]=true
set CAIBossRole[i]=false
set n=n+1
endif
set i=i+1
endloop
set i=0
loop
exitwhen i>=10
if not CAIActive[i] and GetPlayerController(Player(i))==MAP_CONTROL_COMPUTER and GetPlayerSlotState(Player(i))==PLAYER_SLOT_STATE_PLAYING and n<5 then
set CAIActive[i]=true
set CAIBossRole[i]=n>=3
set n=n+1
endif
set i=i+1
endloop
endfunction''')
    b=function(source,'CAIStart').replace('set score=CAIRank(GetUnitTypeId(u))','set score=CAIRoleRank(pid,GetUnitTypeId(u))')
    b=b.replace('set CAIRunner=pid','if CAIBossRole[pid] then\ncall DisplayTimedTextToForce(GetPlayersAll(),10.,"AI role: BOSS burst specialist.")\nendif')
    update('CAIStart',b)
    # Reserve specialist ultimates for bosses/heroes, including mirror opponents.
    b=function(source,'CAISpells')
    marker="if id=='E020' then"
    kai=b.index(marker);end=b.index("if id=='H02H' then",kai)
    b=b[:kai]+'''if id=='E020' then
if CAIBossRole[GetPlayerId(GetOwningPlayer(h))] and not IsUnitType(target,UNIT_TYPE_HERO) and not CAIMainBoss(target) then
return CAICast(h,target,'A0FB',"renew",1)
endif
if GetUnitAbilityLevel(h,'B00G')==0 and CAICast(h,target,'A0HI',"berserk",0) then
return true
endif
if CAICast(h,target,'A0HF',"renewoff",2) then
return true
endif
if not CAINear(h,GetUnitX(target),GetUnitY(target),400.) and CAICast(h,target,'A0FB',"renew",1) then
return true
endif
if CAICast(h,target,'A0HH',"thunderbolt",1) then
return true
endif
if CAICast(h,target,'A0FB',"renew",1) then
return true
endif
endif
'''+b[end:]
    b=b.replace("if id=='E06N' then",'''if id=='E06N' then
if CAIBossRole[GetPlayerId(GetOwningPlayer(h))] and not IsUnitType(target,UNIT_TYPE_HERO) and not CAIMainBoss(target) then
return CAICast(h,target,'A0R5',"absorb",2)
endif''')
    update('CAISpells',b)
    update('CAIGrow',grow)
    b=function(source,'CAIObserve')
    update('CAIObserve',b.replace("GetUnitAbilityLevel(e,'Aloc')==0 and", "GetUnitAbilityLevel(e,'Aloc')==0 and GetUnitAbilityLevel(e,'Avul')==0 and"))
    b=function(source,'CAIFarmRoom')
    condition='if CAITime>=CAIRoomUntil[pid] or GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.3 or (CAITime-CAIRoomStarted[pid]>15. and cost>0 and GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)>=cost+5000 and GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_LUMBER)>=CAIPlannedLumber) then'
    b=re.sub(r'^if CAITime>=CAIRoomUntil\[pid\].* then$',condition,b,flags=re.M)
    b=b.replace('call IssueTargetOrder(h,"attack",enemy)','call CAIAttackOrder(h,enemy)').replace('call IssuePointOrder(h,"attack",x,y)','call CAIMoveOrder(h,"attack",x,y)')
    update('CAIFarmRoom',b)
    update('CAIEnterRoom',function(source,'CAIEnterRoom').replace('CAITime+60.','CAITime+90.'))
    update('CAIRecall',function(source,'CAIRecall').replace('set CAIRoomRetry[pid]=CAITime+15.','set CAIRoomRetry[pid]=CAITime+2.'))
    # Retain mirror ownership, cooldown, health, skill and damage checks; remove
    # only the obsolete single-runner restriction after the first wave.
    update('CAIMirrorChoice',function(source,'CAIMirrorChoice').replace(' or (CAIFirstWaveSeen and pid!=CAIRunner)',''))
    update('CAIFightMirror',function(source,'CAIFightMirror').replace('call IssueTargetOrder(h,"attack",enemy)','call CAIAttackOrder(h,enemy)'))
    for name in ['CAIBuy','CAICraft','CAIWater']:
        b=function(source,name)
        b=b.replace('call IssuePointOrder(h,"move",','call CAIMoveOrder(h,"move",')
        update(name,b)
    b=function(source,'CAITick')
    b=b.replace('local integer tries=0\n','').replace('local unit enemy\n','local unit enemy\nlocal unit threat\n')
    b=re.sub(r'^set danger=.*$', 'set danger=CAIWantDefense(remaining)', b,flags=re.M)
    b=re.sub(r'if CAITime>=CAIRotateAt.*?(?=loop\nexitwhen pid>=10)', '',b,flags=re.S)
    b=b.replace('set enemy=CAIFindEnemy(h,bx,by,3000.)','''set threat=CAIFindEnemy(h,bx,by,3000.)
if CAIBossRole[pid] then
set enemy=CAIFindBoss(h,bx,by)
if enemy!=null then
set threat=enemy
endif
endif
set enemy=threat''')
    b=b.replace('if danger or (CAIMirrorSlot','if danger or threat!=null or (CAIMirrorSlot')
    # Room targets are for combat sampling only, never for castle defense.
    b=b.replace('set CAIMode[pid]="defense"','set enemy=threat\nset CAIMode[pid]="defense"')
    b=b.replace('if not CAINear(h,bx,by,1700.) then','if CAIRoom[pid]>0 or CAIMirrorSlot[pid]>0 or not CAINear(h,bx,by,3600.) then',1)
    b=b.replace('set allowGrow=not CAIHold and (not CAIFirstWaveSeen or pid==CAIRunner)','set allowGrow=CAIAllowGrowth(pid)')
    b=b.replace('call IssuePointOrder(h,"move",','call CAIMoveOrder(h,"move",').replace('call IssuePointOrder(h,"attack",','call CAIMoveOrder(h,"attack",').replace('call IssueTargetOrder(h,"attack",enemy)','call CAIAttackOrder(h,enemy)')
    b=b.replace('set worked=CAISpells(h,enemy)','if enemy!=null then\nset worked=CAISpells(h,enemy)\nendif')
    watchdog='''elseif allowGrow then
if CAINear(h,CAILastX[pid],CAILastY[pid],20.) and CAIRoom[pid]==0 and CAIMirrorSlot[pid]==0 then
set CAIStuck[pid]=CAIStuck[pid]+.5
else
set CAIStuck[pid]=0.
endif
set CAILastX[pid]=GetUnitX(h)
set CAILastY[pid]=GetUnitY(h)
if CAIStuck[pid]>=10. then
call IssueImmediateOrder(h,"stop")
set worked=CAIRecall(h)
set CAIStuck[pid]=0.
endif'''
    b=b.replace('elseif allowGrow then',watchdog).replace('set enemy=null\nendfunction','set enemy=null\nset threat=null\nendfunction')
    update('CAITick',b)
    b=function(source,'CAIChat')
    b=b.replace('local integer i=0','local integer i=0\nlocal integer nextCost=0')
    b=b.replace('if CAIMeasured then','call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"AI6: defense first; continuous gold/XP for endgame equipment. Readiness is display-only.")\nif CAIMeasured then')
    b=b.replace('if CAIActive[i] then','if CAIActive[i] then\nif CAIBossRole[i] then\ncall DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Role: BOSS burst")\nelse\ncall DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Role: castle defense")\nendif\nset nextCost=CAINextGearCost(udg_Y_Xiong[i+1])\ncall DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Next gear gold: "+I2S(nextCost)+"; lumber: "+I2S(CAIPlannedLumber))')
    update('CAIChat',b)
    b=function(source,'InitCustomPlayerSlots')
    for pid in [5,6]:
        old=f'call SetPlayerController(Player({pid}),MAP_CONTROL_USER)'
        assert old in b
        b=b.replace(old,f'call SetPlayerController(Player({pid}),MAP_CONTROL_COMPUTER)')
    update('InitCustomPlayerSlots',b)
    # Byte-for-byte preservation of every other pre-existing function.
    preserved=0
    current={m[1]:m[0] for m in re.finditer(r'^function (\w+) takes .*?^endfunction',source,re.M|re.S)}
    for m in re.finditer(r'^function (\w+) takes .*?^endfunction',original,re.M|re.S):
        if m[1] not in updated:
            assert current[m[1]]==m[0],m[1]
            preserved+=1
    return source,dict(changed_functions=updated,preserved_functions=preserved)

def lobby(data):
    from objects import Reader
    r=Reader(data);assert r.n()==25
    r.n();r.n()
    for _ in range(4):r.s()
    r.n('8f');r.n('4i');r.n('2i');r.n();r.n('c');r.n()
    for _ in range(4):r.s()
    r.n();r.s()
    for _ in range(3):r.s()
    r.n();r.n('3f');r.n('4B');r.n();r.s();r.n('c');r.n('4B')
    count=r.n();out=bytearray(data);changes=[]
    for _ in range(count):
        pid=r.n();offset=r.p;typ=r.n();r.n();r.n();r.s();r.n('2f');r.n('2I')
        if pid in [5,6]:struct.pack_into('<i',out,offset,2);changes.append(pid)
    assert changes==[5,6]
    return bytes(out)

def build(base=BASE):
    backup=Path('output/backups/AI5_baseline.w3x')
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():shutil.copyfile(base,backup)
    assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(base.read_bytes()).digest(),'AI5 baseline changed; inspect before replacing backup'
    archive=MPQ(base);script=archive.read('war3map.j');info=archive.read('war3map.w3i');archive.close()
    patched,manifest=patch(script.decode('latin1'))
    j=Path('output/war3map_ai6.j');j.write_bytes(patched.encode('latin1'))
    w3i=Path('output/war3map_ai6.w3i');w3i.write_bytes(lobby(info))
    shutil.copyfile(base,DEST)
    from mpq import d
    d.SFileAddFileEx.argtypes=[c.c_void_p,c.c_wchar_p,c.c_char_p,c.c_uint32,c.c_uint32,c.c_uint32];d.SFileAddFileEx.restype=c.c_bool
    handle=c.c_void_p();assert d.SFileOpenArchive(str(DEST.resolve()),0,0,c.byref(handle)),c.get_last_error()
    try:
        assert d.SFileAddFileEx(handle,str(j.resolve()),b'war3map.j',0x80000200,2,2),c.get_last_error()
        assert d.SFileAddFileEx(handle,str(w3i.resolve()),b'war3map.w3i',0x80000200,2,2),c.get_last_error()
    finally:d.SFileCloseArchive(handle)
    manifest.update(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),modified_sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),modified_entries=['war3map.j','war3map.w3i'],defenders=['H00Q','H00O','N02F'],boss_specialists=['E020','E06N'],computer_slots=[6,7,8,9,10],runtime_tested=False)
    Path('output/continuous_build_manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=BASE);build(p.parse_args().base)
