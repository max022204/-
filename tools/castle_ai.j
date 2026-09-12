// Local defense AI. Uses original hero selection, pickup quests and item recipes.
function CAIAlive takes unit u returns boolean
return u!=null and GetWidgetLife(u)>.405 and not IsUnitType(u,UNIT_TYPE_DEAD)
endfunction
function CAIHas takes unit h, integer id returns boolean
return UnitHasItemOfTypeBJ(h,id)
endfunction
function CAINear takes unit h, real x, real y, real r returns boolean
local real dx=GetUnitX(h)-x
local real dy=GetUnitY(h)-y
return dx*dx+dy*dy<=r*r
endfunction
function CAIFindEnemy takes unit h, real x, real y, real radius returns unit
local group g=CreateGroup()
local unit u
local unit best=null
local real score
local real distance=100000000.
call GroupEnumUnitsInRange(g,x,y,radius,null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if CAIAlive(u) and IsUnitEnemy(u,GetOwningPlayer(h)) and not IsUnitHidden(u) and GetUnitAbilityLevel(u,'Aloc')==0 and GetUnitAbilityLevel(u,'Avul')==0 then
set score=(GetUnitX(u)-x)*(GetUnitX(u)-x)+(GetUnitY(u)-y)*(GetUnitY(u)-y)
if score<distance then
set best=u
set distance=score
endif
endif
endloop
call DestroyGroup(g)
set g=null
set u=null
return best
endfunction
function CAIBuy takes unit h, integer id, integer gold, integer lumber, real x, real y returns boolean
local player p=GetOwningPlayer(h)
local item it
if CAIPlanOnly then
set CAIPlannedCost=gold+CAIPlannedExtra
set p=null
return true
endif
if not CAINear(h,x,y,550.) then
call IssuePointOrder(h,"move",x,y)
set p=null
return true
endif
if GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)<gold or GetPlayerState(p,PLAYER_STATE_RESOURCE_LUMBER)<lumber then
set p=null
return false
endif
call SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)-gold)
call SetPlayerState(p,PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(p,PLAYER_STATE_RESOURCE_LUMBER)-lumber)
set it=CreateItem(id,GetUnitX(h),GetUnitY(h))
if not UnitAddItem(h,it) then
call RemoveItem(it)
call SetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(p,PLAYER_STATE_RESOURCE_GOLD)+gold)
call SetPlayerState(p,PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(p,PLAYER_STATE_RESOURCE_LUMBER)+lumber)
endif
set it=null
set p=null
return true
endfunction
function CAIGear takes unit h returns boolean
local integer gold=GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)
local integer jade=0
local integer i=1
if CAIPlanOnly then
set gold=2000000000
endif
loop
exitwhen i>16
if CAIHas(h,udg_yu2[i]) then
set jade=i
endif
set i=i+1
endloop
// Original pickup triggers perform every upgrade and validate the recipe.
if jade==0 then
if CAIHas(h,'I00K') and CAIHas(h,'I00E') and CAIHas(h,'I00L') then
if gold>=22000 then
return CAIBuy(h,'I01N',22000,0,4800.,3520.)
endif
return false
endif
if not CAIHas(h,'I00I') and not CAIHas(h,'I00H') and not CAIHas(h,'I00G') and not CAIHas(h,'I00B') and not CAIHas(h,'I00K') then
if gold>=1000 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'I00I',1000,0,4416.,3520.)
endif
elseif not CAIHas(h,'I00J') and not CAIHas(h,'I00C') and not CAIHas(h,'I00D') and not CAIHas(h,'I00F') and not CAIHas(h,'I00E') then
if gold>=2000 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'I00J',2000,0,4416.,3520.)
endif
elseif not CAIHas(h,'I00P') and not CAIHas(h,'I00M') and not CAIHas(h,'I00N') and not CAIHas(h,'I00O') and not CAIHas(h,'I00L') then
if gold>=1000 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'I00P',1000,0,4416.,3520.)
endif
elseif gold>=3000 then
if not CAIHas(h,'I00K') then
return CAIBuy(h,'I01H',3000,0,4800.,3520.)
elseif not CAIHas(h,'I00E') then
return CAIBuy(h,'I01I',3000,0,4800.,3520.)
elseif not CAIHas(h,'I00L') then
return CAIBuy(h,'I01J',3000,0,4800.,3520.)
endif
endif
elseif not CAIHas(h,'I00R') and not CAIHas(h,'I00W') and not CAIHas(h,'I00S') and not CAIHas(h,'I00T') and not CAIHas(h,'I00U') and not CAIHas(h,'I00V') then
if gold>=3000 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'I00R',3000,0,4416.,3520.)
endif
elseif not CAIHas(h,'I00V') and gold>=3000 then
return CAIBuy(h,'I01K',3000,0,4800.,3520.)
elseif GetHeroInt(h,false)>GetHeroAgi(h,false) and GetHeroInt(h,false)>GetHeroStr(h,false) and not CAIHas(h,'pmna') and gold>=200 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'pmna',200,0,3520.,4096.)
elseif GetUnitTypeId(h)!='H00O' and not CAIHas(h,'I01B') and not CAIHas(h,'I01D') and not CAIHas(h,'I01E') and not CAIHas(h,'I01C') and not CAIHas(h,'I01F') and gold>=13000 and UnitInventoryCount(h)<5 then
return CAIBuy(h,'I01B',13000,0,4416.,3520.)
elseif (CAIHas(h,'I01B') or CAIHas(h,'I01D') or CAIHas(h,'I01E') or CAIHas(h,'I01C')) and gold>=3000 then
return CAIBuy(h,'I01L',3000,0,4800.,3520.)
elseif jade>0 and jade<16 and gold>=60000+10000*jade then
// This voucher has zero purchase cost; the original trigger deducts the enhancement cost.
if CAIPlanOnly then
set CAIPlannedExtra=60000+10000*jade
endif
return CAIBuy(h,'I0A8',0,0,4800.,3520.)
endif
return false
endfunction
function CAIWater takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local boolean full=CAIHas(h,'bzbf')
local boolean result=false
if CAIHas(h,'bzbe') then
call IssuePointOrder(h,"move",1712.,-272.)
return true
endif
if CAIHas(h,'bzbf') or UnitInventoryCount(h)<5 then
set result=CAIBuy(h,'I03Y',0,0,GetUnitX(gg_unit_n00A_0077),GetUnitY(gg_unit_n00A_0077))
if full and not CAIHas(h,'bzbf') then
set CAIWaterDone[pid]=CAIWaterDone[pid]+1
endif
return result
endif
return false
endfunction
function CAICast takes unit h, unit target, integer id, string order, integer mode returns boolean
local integer level=GetUnitAbilityLevel(h,id)
local integer pid=GetPlayerId(GetOwningPlayer(h))
local boolean ok=false
if level<=0 or EXGetAbilityState(EXGetUnitAbility(h,id),1)>.05 then
return false
endif
if mode==0 then
set ok=IssueImmediateOrder(h,order)
elseif mode==1 and target!=null then
set ok=IssueTargetOrder(h,order,target)
elseif mode==2 and target!=null then
set ok=IssuePointOrder(h,order,GetUnitX(target),GetUnitY(target))
elseif mode==3 then
set ok=IssuePointOrder(h,order,GetUnitX(gg_unit_hcas_0007),GetUnitY(gg_unit_hcas_0007))
endif
if ok then
set CAIBusy[pid]=CAITime+1.5
if id=='A073' then
set CAIBusy[pid]=CAITime+10.
endif
endif
return ok
endfunction
// Generated functions CAILearn and CAISpells are inserted here.
// @GENERATED_SPELLS@
function CAISummons takes unit h, unit target returns nothing
local group g=CreateGroup()
local unit u
call GroupEnumUnitsOfPlayer(g,GetOwningPlayer(h),null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if u!=h and CAIAlive(u) and IsUnitType(u,UNIT_TYPE_SUMMONED) and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and GetUnitAbilityLevel(u,'Aloc')==0 then
if target!=null then
call IssuePointOrder(u,"attack",GetUnitX(target),GetUnitY(target))
else
call IssuePointOrder(u,"attack",GetUnitX(gg_unit_hcas_0007),GetUnitY(gg_unit_hcas_0007))
endif
endif
endloop
call DestroyGroup(g)
set g=null
set u=null
endfunction
function CAITick takes nothing returns nothing
local integer pid=0
local integer tries=0
local unit h
local unit enemy
local boolean danger=false
local boolean worked=false
local boolean allowGrow=false
local real remaining
local real bx=GetUnitX(gg_unit_hcas_0007)
local real by=GetUnitY(gg_unit_hcas_0007)
set CAITime=CAITime+.5
if not CAIAlive(gg_unit_hcas_0007) then
return
endif
call CAIObserve()
set remaining=TimerGetRemaining(udg_Dmb_jsq[1])
set danger=CAIWaveActive or GetWidgetLife(gg_unit_hcas_0007)<GetUnitState(gg_unit_hcas_0007,UNIT_STATE_MAX_LIFE)*.8 or (udg_boshu>0 and remaining>0. and remaining<=20.)
if CAITime>=CAIRotateAt and CAIRunner>=0 then
set h=udg_Y_Xiong[CAIRunner+1]
if not CAIAlive(h) or (CAINear(h,bx,by,1800.) and not CAIHas(h,'bzbe') and not CAIHas(h,'bzbf') and CAIRoom[CAIRunner]==0) then
loop
set CAIRunner=ModuloInteger(CAIRunner+1,10)
set tries=tries+1
exitwhen CAIActive[CAIRunner] or tries>=10
endloop
set CAIRotateAt=CAITime+60.
endif
endif
loop
exitwhen pid>=10
if CAIActive[pid] then
set h=udg_Y_Xiong[pid+1]
if CAIAlive(h) then
call CAILearn(h)
set enemy=CAIFindEnemy(h,bx,by,3000.)
set worked=false
// Recall must interrupt farming/channeling promptly, not wait for cast locks.
if danger then
set CAIMode[pid]="defense"
set CAIQuiet[pid]=0.
if not CAINear(h,bx,by,1700.) then
set worked=CAIRecall(h)
if not worked then
call IssuePointOrder(h,"move",bx,by)
endif
set worked=true
elseif CAITime>=CAIBusy[pid] then
set worked=CAISpells(h,enemy)
if not worked and enemy!=null then
call IssueTargetOrder(h,"attack",enemy)
set worked=true
endif
if not worked and not CAINear(h,bx,by,650.) then
call IssuePointOrder(h,"attack",bx,by)
endif
endif
elseif CAITime>=CAIBusy[pid] then
set CAIQuiet[pid]=CAIQuiet[pid]+.5
set allowGrow=not CAIHold and (not CAIFirstWaveSeen or pid==CAIRunner)
if GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.3 then
set CAIRecover[pid]=true
endif
if CAIRecover[pid] and GetWidgetLife(h)>=GetUnitState(h,UNIT_STATE_MAX_LIFE)*.75 then
set CAIRecover[pid]=false
endif
if CAIRecover[pid] then
set CAIMode[pid]="recover"
if not CAINear(h,bx,by,1700.) then
set worked=CAIRecall(h)
else
set worked=CAISpells(h,null)
endif
set worked=true
elseif allowGrow then
set worked=CAIGrow(h)
elseif CAIRoom[pid]>0 or not CAINear(h,bx,by,1700.) then
set worked=CAIRecall(h)
endif
if not worked then
set CAIMode[pid]="guard"
if not CAINear(h,bx,by,650.) then
call IssuePointOrder(h,"attack",bx,by)
endif
endif
endif
if ModuloInteger(R2I(CAITime*2.),10)==0 then
if CAIRoom[pid]>0 then
set enemy=CAIRoomEnemy(h,CAIRoom[pid])
endif
call CAISummons(h,enemy)
endif
endif
endif
set pid=pid+1
endloop
set h=null
set enemy=null
endfunction
function CAIChat takes nothing returns nothing
local integer i=0
if GetEventPlayerChatString()=="-ai hold" then
set CAIHold=true
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,10.,"AI: defense only.")
elseif GetEventPlayerChatString()=="-ai auto" then
set CAIHold=false
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,10.,"AI: defense first; tasks and equipment enabled.")
elseif GetEventPlayerChatString()=="-ai factor 2" then
set CAIFactor=2.
elseif GetEventPlayerChatString()=="-ai factor 2.5" then
set CAIFactor=2.5
elseif GetEventPlayerChatString()=="-ai factor 3" then
set CAIFactor=3.
else
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Wave "+I2S(CAITargetWave)+" target HP/ATK/ARM: "+R2S(CAITargetHP)+" / "+R2S(CAITargetAttack)+" / "+R2S(CAITargetArmor)+"; AI x "+R2S(CAIFactor)+" >= enemy")
if CAIMeasured then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Target source: observed live units (includes bosses).")
else
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"Target source: pre-wave estimate; corrected when enemies spawn.")
endif
loop
exitwhen i>=10
if CAIActive[i] then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"AI "+I2S(i+1)+": "+GetUnitName(udg_Y_Xiong[i+1])+" Lv "+I2S(GetHeroLevel(udg_Y_Xiong[i+1]))+"; "+CAIMode[i]+"; readiness "+I2S(R2I(CAIReadiness(udg_Y_Xiong[i+1])*100.))+"%; water "+I2S(CAIWaterDone[i]))
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,20.,"HP/ATK/ARM: "+R2S(GetUnitState(udg_Y_Xiong[i+1],UNIT_STATE_MAX_LIFE))+" / "+R2S(CAIAttack(udg_Y_Xiong[i+1]))+" / "+R2S(CAIArmor(udg_Y_Xiong[i+1])))
endif
set i=i+1
endloop
endif
endfunction
function CAIStart takes nothing returns nothing
local integer pid=0
local integer rank=0
local integer bestScore
local integer score
local unit u
local unit best
local group g
if not IsTriggerEnabled(gg_trg_xuanzjs01) or udg_Suiji_zs[3]==0 then
return
endif
call PauseTimer(GetExpiredTimer())
call DestroyTimer(GetExpiredTimer())
loop
exitwhen pid>=10
if CAIActive[pid] then
set best=null
set bestScore=-1
set g=CreateGroup()
call GroupEnumUnitsInRect(g,gg_rct______________000,null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if CAIAlive(u) and IsUnitType(u,UNIT_TYPE_HERO) and not IsUnitHidden(u) and GetOwningPlayer(u)==Player(PLAYER_NEUTRAL_PASSIVE) then
set score=CAIRank(GetUnitTypeId(u))
if score>bestScore then
set best=u
set bestScore=score
endif
endif
endloop
call DestroyGroup(g)
if best!=null and bestScore>0 then
set udg_xzjs_uint[pid+1]=best
call CAISelect(Player(pid),best)
call SetUnitState(udg_Y_Xiong[pid+1],UNIT_STATE_MANA,GetUnitState(udg_Y_Xiong[pid+1],UNIT_STATE_MAX_MANA))
call DisplayTimedTextToForce(GetPlayersAll(),10.,"AI: "+GetHeroProperName(udg_Y_Xiong[pid+1])+" guarding the castle.")
set CAIRunner=pid
endif
endif
set pid=pid+1
endloop
call TimerStart(CreateTimer(),.5,true,function CAITick)
set u=null
set best=null
set g=null
endfunction
function CAIBoot takes nothing returns nothing
local integer i=0
local trigger chat=CreateTrigger()
// No chat password is needed; keep both original and hidden alternate heroes.
set udg_YINc_buff[1]=true
set udg_YINc_buff[2]=true
set udg_YINc_buff[3]=true
set udg_YINc_buff[4]=true
loop
exitwhen i>=10
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai status",true)
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai hold",true)
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai auto",true)
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai factor 2",true)
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai factor 2.5",true)
call TriggerRegisterPlayerChatEvent(chat,Player(i),"-ai factor 3",true)
set i=i+1
endloop
call TriggerAddAction(chat,function CAIChat)
call TimerStart(CreateTimer(),1.,true,function CAIStart)
set chat=null
endfunction
