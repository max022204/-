"""Generate reviewable AI8 JASS only. Never writes a map archive."""
import hashlib,json,re,struct
from pathlib import Path
from build_continuous import patch,function

ROSTER=[('H00Q','support'),('H046','support'),('H00O','control'),('E00L','control'),('N02F','clear'),('E020','burst'),('E06N','burst'),('E02L','tank')]

def prepare(original):
    source,manifest=patch(original)
    changed=[]
    def update(name,body):
        nonlocal source
        source=source.replace(function(source,name),body,1)
        changed.append(name)
    globals_='integer array CAI8Role\ninteger array CAI8Hero\ninteger array CAI8TripKind\ninteger array CAI8Step\nunit array CAI8Target\nunit CAI8CC=null\nreal CAI8CCUntil=0.\n'
    globals_+=''.join('real array CAI8'+n+'\n' for n in ['Until','Retry','Progress','LastHP','LootUntil'])
    source=source.replace('endglobals',globals_+'endglobals',1)
    init='\n'.join(f"set CAI8Hero[{i}]='{hero}'\nset CAI8Role[{i}]={dict(support=1,control=2,clear=3,burst=4,tank=5)[role]}" for i,(hero,role) in enumerate(ROSTER))
    update('CAIPrepare','''function CAIPrepare takes nothing returns nothing
local integer i=0
local integer n=0
set CAISelectionContext=CreateTrigger()
'''+init+'''
loop
exitwhen i>=10
if GetPlayerController(Player(i))==MAP_CONTROL_COMPUTER and GetPlayerSlotState(Player(i))==PLAYER_SLOT_STATE_PLAYING and n<8 then
set CAIActive[i]=true
set CAI8Assigned[i]=n
set CAIBossRole[i]=CAI8Role[n]==4
set n=n+1
endif
set i=i+1
endloop
endfunction''')
    source=source.replace('endglobals','integer array CAI8Assigned\nendglobals',1)
    update('CAIRoleRank','''function CAIRoleRank takes integer pid, integer id returns integer
local integer i=0
if id==CAI8Hero[CAI8Assigned[pid]] then
return 10000
endif
// Preserve the other seven assigned heroes if a human took this one's pick.
loop
exitwhen i>=8
if id==CAI8Hero[i] then
return 1
endif
set i=i+1
endloop
return CAIRank(id)
endfunction''')
    source=source.replace('function CAISpells takes',Path('tools/ai8_roles.j').read_text('utf-8')+'\nfunction CAISpells takes',1)
    b=function(source,'CAISpells')
    # Insert after all locals, before original executable statements.
    lines=b.splitlines();idx=1
    while lines[idx].startswith('local '):idx+=1
    lines[idx:idx]=['if CAI8RoleCast(h,target) then','return true','endif']
    b='\n'.join(lines)
    # These spells now belong exclusively to the role handler (shared CC lock).
    for ability in ['A0B0','A0GW','A06H','A057','A058','A0U3']:
        b=re.sub(r"if CAICast\(h,target,'"+ability+r"',[^\n]+\) then\nreturn true\nendif\n",'',b)
    update('CAISpells',b)
    source=source.replace('function CAIGrow takes',Path('tools/ai8_adventures.j').read_text('utf-8')+'\nfunction CAIGrow takes',1)
    b=function(source,'CAIGrow').replace('if CAIMirrorSlot[pid]>0 then','if CAI8TripKind[pid]>0 then\nreturn CAI8Trip(h)\nendif\nif CAIMirrorSlot[pid]>0 then',1)
    b=b.replace('// Mirror safety/DPS', '''if not CAI8Equipped(h) then
set result=CAIGear(h)
if result then
return true
endif
return CAIWater(h)
endif
if CAI8StartTrip(h) then
return true
endif
// Mirror safety/DPS''')
    update('CAIGrow',b)
    b=function(source,'CAIRecall').replace('set CAIRoom[pid]=0','set CAI8TripKind[pid]=0\nset CAI8Target[pid]=null\nset CAI8Retry[pid]=CAITime+15.\nset CAIRoom[pid]=0',1)
    update('CAIRecall',b)
    b=function(source,'CAITick').replace('if CAIRoom[pid]>0 or CAIMirrorSlot[pid]>0 or not CAINear','if CAI8TripKind[pid]>0 or CAIRoom[pid]>0 or CAIMirrorSlot[pid]>0 or not CAINear',1)
    b=b.replace('call CAIWatchCombat(h,enemy)','if CAI8TripKind[pid]>0 then\nset enemy=CAI8Target[pid]\nendif\ncall CAIWatchCombat(h,enemy)',1)
    b=b.replace('set CAIMode[pid]="defense"','''set CAIMode[pid]="defense"
if CAI8TripKind[pid]>0 and CAINear(h,bx,by,1700.) then
set CAI8TripKind[pid]=0
set CAI8Target[pid]=null
set CAI8Retry[pid]=CAITime+15.
endif''',1)
    b=b.replace('and CAIRoom[pid]==0 and CAIMirrorSlot[pid]==0 then','and CAIRoom[pid]==0 and CAIMirrorSlot[pid]==0 and CAI8TripKind[pid]==0 then')
    b=b.replace('set CAIWatchTarget[pid]=null','set CAI8TripKind[pid]=0\nset CAI8Target[pid]=null\nset CAIWatchTarget[pid]=null')
    update('CAITick',b)
    b=function(source,'InitCustomPlayerSlots')
    for pid in [2,3,4]:
        old=f'call SetPlayerController(Player({pid}),MAP_CONTROL_USER)'
        assert old in b
        b=b.replace(old,f'call SetPlayerController(Player({pid}),MAP_CONTROL_COMPUTER)')
    update('InitCustomPlayerSlots',b)
    update('CAIChat',function(source,'CAIChat').replace('AI6:','AI8:').replace('Role: castle defense','Role: assigned support / control / clear / tank'))
    changed=set(changed+manifest['changed_functions'])
    preserved=0
    current={m[1]:m[0] for m in re.finditer(r'^function (\w+) takes .*?^endfunction',source,re.M|re.S)}
    for m in re.finditer(r'^function (\w+) takes .*?^endfunction',original.replace('\r\n','\n'),re.M|re.S):
        if m[1] not in changed:
            assert current[m[1]]==m[0],m[1]
            preserved+=1
    return source,dict(changed_functions=sorted(changed),preserved_functions=preserved,roster=ROSTER,computer_slots=list(range(3,11)),human_slots=[1,2],packaged=False,runtime_tested=False)

def lobby_draft(data):
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
        if pid in range(2,10):
            struct.pack_into('<i',out,offset,2)
            if typ!=2:changes.append(offset)
    allowed={p+j for p in changes for j in range(4)}
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
    return bytes(out),changes

if __name__=='__main__':
    baseline=Path('output/backups/ai5_script.j').read_bytes()
    source,manifest=prepare(baseline.decode('latin1'))
    target=Path('output/war3map_ai8.j')
    target.write_bytes(source.encode('latin1'))
    manifest['script_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    from mpq import MPQ
    archive=MPQ(Path('output/backups/AI5_baseline.w3x'))
    try:info=archive.read('war3map.w3i')
    finally:archive.close()
    draft,offsets=lobby_draft(info)
    Path('output/war3map_ai8.w3i').write_bytes(draft)
    manifest['lobby_changed_controller_offsets']=offsets
    manifest['lobby_sha256']=hashlib.sha256(draft).hexdigest()
    Path('output/ai8_draft_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
