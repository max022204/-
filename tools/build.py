import re,json,ctypes as c,shutil,hashlib,struct
from pathlib import Path
src=Path('extracted/war3map.j').read_bytes().decode('latin1').replace('\r\n','\n')
units=json.loads(Path('output/units.json').read_text('utf-8'))
abilities=json.loads(Path('output/abilities.json').read_text('utf-8'))
roster={int(n):bytes.fromhex(h).decode('ascii') for n,h in re.findall(r'set udg_Yx_Lxing\[(\d+)\]=\$([A-F0-9]{8})',src)}
def raw(id):return "'"+id+"'"
def score(id):
 u=units[id];text=' '.join(abilities.get(a,{}).get('Ubertip','') for a in u.get('heroAbilList','').split(','))
 return int(100+float(u.get('rangeN1',0))/30+sum(8 for s in ['范围','周围','晕眩','减速','恢复','分裂','持续','召唤'] if s in text))
rank={id:score(id) for id in roster.values()}
rank.update({'H00Q':1000,'H00O':999,'N02F':998})
Path('output/ai_ranking.json').write_text(json.dumps(sorted([{'id':k,'name':units[k].get('Propernames',units[k].get('Name','')),'score':v} for k,v in rank.items()],key=lambda a:-a['score']),ensure_ascii=False,indent=2),'utf-8')
globals='''
boolean array CAIActive
real array CAIBusy
real array CAIQuiet
real CAITime=0.
real CAIRotateAt=60.
integer CAIRunner=-1
boolean CAIHold=false
trigger CAISelectionContext=null
boolean CAIPlanOnly=false
integer CAIPlannedCost=0
integer CAIPlannedExtra=0
integer array CAIWaterDone
integer array CAIRoom
real array CAIRoomUntil
real array CAIRoomStarted
real array CAIRoomRetry
real array CAIReturnAfter
real CAIFactor=2.5
real CAITargetHP=1.
real CAITargetAttack=1.
real CAITargetArmor=0.
boolean CAIWaveActive=false
boolean CAIMeasured=false
boolean CAIFirstWaveSeen=false
integer CAITargetWave=1
real array CAISeenHP
real array CAISeenAttack
real array CAISeenArmor
string array CAIMode
boolean array CAIRecover
'''
early='''
function CAIHumanOrBot takes player p returns boolean
return GetPlayerController(p)==MAP_CONTROL_USER or CAIActive[GetPlayerId(p)]
endfunction
function CAIPrepare takes nothing returns nothing
local integer i=0
local integer n=0
set CAISelectionContext=CreateTrigger()
loop
exitwhen i>=10
if GetPlayerController(Player(i))==MAP_CONTROL_COMPUTER and GetPlayerSlotState(Player(i))==PLAYER_SLOT_STATE_PLAYING and n<3 then
set CAIActive[i]=true
set n=n+1
endif
set i=i+1
endloop
endfunction
'''
# Enable computer participants only where the original checks a gameplay owner or roster iterator.
# Host-only menus and platform persistence remain unchanged.
patterns=['GetOwningPlayer(GetAttacker())','GetOwningPlayer(GetEventDamageSource())','ConvertedPlayer(GetForLoopIndexA())']
for p in patterns:
 src=src.replace('GetPlayerController('+p+')==MAP_CONTROL_USER','CAIHumanOrBot('+p+')')
# Keep each original byte, including mixed-encoding model resource names.
src=src.replace('endglobals',''+globals+'endglobals\n'+early,1)
select=re.search(r'function Trig_xuanzjs01Actions takes nothing returns nothing\n.*?\nendfunction',src,re.S)[0]
select=select.replace('function Trig_xuanzjs01Actions takes nothing returns nothing','function CAISelect takes player aiPlayer, unit aiHero returns nothing').replace('GetTriggerPlayer()','aiPlayer').replace('GetTriggerUnit()','aiHero').replace('GetTriggeringTrigger()','CAISelectionContext')
rankfn='function CAIRank takes integer id returns integer\n'
for id,s in rank.items():rankfn+='if id=='+raw(id)+' then\nreturn '+str(s)+'\nendif\n'
rankfn+='return -1\nendfunction\n'
learn='function CAILearn takes unit h returns nothing\nlocal integer id=GetUnitTypeId(h)\n'
cast='function CAISpells takes unit h, unit target returns boolean\nlocal integer id=GetUnitTypeId(h)\nif target==null then\nif id==\'H00Q\' and GetWidgetLife(gg_unit_hcas_0007)<GetUnitState(gg_unit_hcas_0007,UNIT_STATE_MAX_LIFE)*.9 then\nreturn CAICast(h,null,\'A0JO\',"healingward",3)\nendif\nreturn false\nendif\n'
mode_by_code={'AHtb':1,'AUfn':1,'ANfb':1,'ANfl':1,'ANso':1,'AHbz':2,'AHfs':2,'AUcs':2,'AOsh':2,'ACtb':2,'ANcs':2,'ANin':2,'AEer':1,'AHtc':0,'AOws':0,'AEsf':0,'ANbr':0,'Aroa':0,'Absk':0,'AOmi':0,'ANcr':0,'Ahwd':3}
fallback={'ANfb':'firebolt'}
for id in roster.values():
 al=units[id].get('heroAbilList','').split(',')
 learn+='if id=='+raw(id)+' then\n'
 for a in al:
  if len(a)==4:learn+='call SelectHeroSkill(h,'+raw(a)+')\n'
 learn+='return\nendif\n'
 cast+='if id=='+raw(id)+' then\n'
 # Ultimates before basic nukes; healing ward before other spells for Hashirama.
 priority=list(reversed(al))
 if id=='H00Q':priority=['A0JO','A073','A0R2','A0R1','A074']
 for aid in priority:
  a=abilities.get(aid,{})
  code=a.get('code','');order=a.get('Order',fallback.get(code,''));mode=mode_by_code.get(code)
  if code=='ANcl':order=a.get('DataF1','');mode={0:0,1:1,2:2,3:2}.get(int(a.get('DataB1','0')))
  if mode is None or not order or order=='channel':continue
  cast+=f'if CAICast(h,target,{raw(aid)},"{order}",{mode}) then\nreturn true\nendif\n'
 cast+='endif\n'
learn+='endfunction\n';cast+='return false\nendfunction\n'
ai=Path('tools/castle_ai.j').read_text('utf-8').replace('// @GENERATED_SPELLS@',learn+cast)
patch=select+'\n'+rankfn+ai
hg=[]
for name in ['Conditions','Actions']:
 block=re.search(r'function Trig_HG'+name+r' takes nothing returns (?:boolean|nothing)\n.*?\nendfunction',src,re.S)[0]
 block=block.replace('Trig_HG'+name+' takes nothing','CAIHG'+name+' takes player aiPlayer').replace('GetTriggerPlayer()','aiPlayer')
 hg.append(block)
growth=Path('tools/growth_ai.j').read_text('utf-8')
wavegen='function CAIWaveForecast takes integer wave returns nothing\nlocal real l=I2R(GetPlayerTechCount(Player(11),\'R001\',true))\n'
waves=json.loads(Path('output/waves.json').read_text('utf-8'))
for n,id in waves.items():
 v=units[id]
 hp=float(v.get('HP',0));attack=float(v.get('dmgplus1',0))+float(v.get('dice1',0))*float(v.get('sides1',0));armor=float(v.get('def',0))
 wavegen+=f'if wave=={n} then\nset CAITargetHP={hp:.3f}*(1.+.5*l)\nset CAITargetAttack={attack:.3f}+{float(v.get("dmgUp1",0)):.3f}*l\nset CAITargetArmor={armor:.3f}+{float(v.get("defUp",0)):.3f}*l\nendif\n'
wavegen+='endfunction\n'
growth=growth.replace('// @FORECAST@',wavegen)
# Growth helpers depend on CAIGear/CAISpells, so insert directly before CAISummons.
patch=patch.replace('function CAISummons takes', '\n'.join(hg)+'\n'+growth+'\nfunction CAISummons takes',1)
src=src.replace('function main takes nothing returns nothing',patch+'\nfunction main takes nothing returns nothing',1)
src=src.replace('call RunInitializationTriggers()','call CAIPrepare()\ncall RunInitializationTriggers()\ncall CAIBoot()',1)
for pid in [7,8,9]:src=src.replace(f'call SetPlayerController(Player({pid}),MAP_CONTROL_USER)',f'call SetPlayerController(Player({pid}),MAP_CONTROL_COMPUTER)')
Path('output/war3map_ai.j').write_bytes(src.encode('latin1'))
# Native StormLib API; modify only a fresh workspace copy.
d=c.WinDLL(str(Path('tools/stormlib/x64/StormLib.dll').resolve()),use_last_error=True)
for n,args in {'SFileOpenArchive':[c.c_wchar_p,c.c_uint32,c.c_uint32,c.POINTER(c.c_void_p)],'SFileAddFileEx':[c.c_void_p,c.c_wchar_p,c.c_char_p,c.c_uint32,c.c_uint32,c.c_uint32],'SFileCloseArchive':[c.c_void_p]}.items():
 f=getattr(d,n);f.argtypes=args;f.restype=c.c_bool
dest=Path('output/000_Bonds737_AI3.w3x');shutil.copyfile('output/original.w3x',dest)
h=c.c_void_p();assert d.SFileOpenArchive(str(dest.resolve()),0,0,c.byref(h)),c.get_last_error()
assert d.SFileAddFileEx(h,str(Path('output/war3map_ai.j').resolve()),b'war3map.j',0x80000200,2,2),c.get_last_error()
assert d.SFileAddFileEx(h,str(Path('output/war3map_ai.w3i').resolve()),b'war3map.w3i',0x80000200,2,2),c.get_last_error()
assert d.SFileCloseArchive(h),c.get_last_error()
manifest={'source_sha256':hashlib.sha256(Path('output/original.w3x').read_bytes()).hexdigest(),'modified_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'modified_entries':['war3map.j','war3map.w3i'],'roster_entries':len(roster),'ai_candidates':len(rank),'runtime_tested':False}
Path('output/build_manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
print(json.dumps(manifest,indent=2))
