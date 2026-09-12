// Read-only runtime unit statistics; no artificial level/stat/wealth boosts.
function CAIAttack takes unit h returns real
return RMaxBJ(1.,GetUnitState(h,ConvertUnitState($15)))
endfunction
function CAIArmor takes unit h returns real
return RMaxBJ(0.,GetUnitState(h,ConvertUnitState($20)))
endfunction
// @FORECAST@
function CAIObserve takes nothing returns nothing
local group g=CreateGroup()
local unit e
local integer wave=IMaxBJ(1,IMinBJ(30,udg_boshu))
local integer kind
set CAIWaveActive=false
set CAITargetWave=wave
call CAIWaveForecast(wave)
call GroupEnumUnitsOfPlayer(g,Player(11),null)
loop
set e=FirstOfGroup(g)
exitwhen e==null
call GroupRemoveUnit(g,e)
if CAIAlive(e) and not IsUnitHidden(e) and GetUnitAbilityLevel(e,'Aloc')==0 and not IsUnitType(e,UNIT_TYPE_STRUCTURE) then
set CAIWaveActive=true
set CAIFirstWaveSeen=true
set kind=GetUnitTypeId(e)
if kind==udg_guai[wave] or IsUnitType(e,UNIT_TYPE_HERO) then
set CAISeenHP[wave]=RMaxBJ(CAISeenHP[wave],GetUnitState(e,UNIT_STATE_MAX_LIFE))
set CAISeenAttack[wave]=RMaxBJ(CAISeenAttack[wave],CAIAttack(e))
set CAISeenArmor[wave]=RMaxBJ(CAISeenArmor[wave],CAIArmor(e))
endif
endif
endloop
set CAIMeasured=CAISeenHP[wave]>0.
if CAIMeasured then
set CAITargetHP=CAISeenHP[wave]
set CAITargetAttack=CAISeenAttack[wave]
set CAITargetArmor=CAISeenArmor[wave]
endif
call DestroyGroup(g)
set e=null
set g=null
endfunction
function CAIReadiness takes unit h returns real
local real ratio=RMinBJ(CAIFactor*GetUnitState(h,UNIT_STATE_MAX_LIFE)/RMaxBJ(1.,CAITargetHP),CAIFactor*CAIAttack(h)/RMaxBJ(1.,CAITargetAttack))
if CAITargetArmor>0. then
set ratio=RMinBJ(ratio,CAIFactor*CAIArmor(h)/CAITargetArmor)
endif
return ratio
endfunction
function CAINextGearCost takes unit h returns integer
local boolean planned
set CAIPlanOnly=true
set CAIPlannedCost=0
set CAIPlannedExtra=0
set planned=CAIGear(h)
set CAIPlanOnly=false
return CAIPlannedCost
endfunction
function CAIRecall takes unit h returns boolean
local player p=GetOwningPlayer(h)
local integer pid=GetPlayerId(p)
if CAIHGConditions(p) and CAITime>=CAIReturnAfter[pid] then
call CAIHGActions(p)
set CAIRoom[pid]=0
set CAIReturnAfter[pid]=CAITime+2.
set CAIRoomRetry[pid]=CAITime+15.
set CAIBusy[pid]=0.
set p=null
return true
endif
set p=null
return false
endfunction
function CAIRoomEnemy takes unit h, integer room returns unit
local group g=CreateGroup()
local unit e
local unit chosen=null
local integer id
local real hp=1000000000.
local real x=1545.6
local real y=4344.2
if room==2 then
set x=4432.9
set y=-1832.2
endif
call GroupEnumUnitsInRange(g,x,y,700.,null)
loop
set e=FirstOfGroup(g)
exitwhen e==null
call GroupRemoveUnit(g,e)
set id=GetUnitTypeId(e)
if CAIAlive(e) and IsUnitEnemy(e,GetOwningPlayer(h)) and ((room==1 and (id=='n038' or id=='n039')) or (room==2 and (id=='n035' or id=='n036'))) then
if GetWidgetLife(e)<hp then
set chosen=e
set hp=GetWidgetLife(e)
endif
endif
endloop
call DestroyGroup(g)
set e=null
set g=null
return chosen
endfunction
function CAIFarmRoom takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local unit enemy
local boolean cast=false
local real x=1545.6
local real y=4344.2
local integer cost=CAINextGearCost(h)
if CAIRoom[pid]==2 then
set x=4432.9
set y=-1832.2
endif
if CAITime>=CAIRoomUntil[pid] or GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.3 or (CAITime-CAIRoomStarted[pid]>15. and (CAIReadiness(h)>=1. or (CAIRoom[pid]==2 and GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)>=IMaxBJ(10000,cost+5000)))) then
set cast=CAIRecall(h)
return true
endif
set enemy=CAIRoomEnemy(h,CAIRoom[pid])
if enemy!=null then
if CAIAttack(enemy)*3.>GetWidgetLife(h) then
set cast=CAIRecall(h)
else
set cast=CAISpells(h,enemy)
if not cast then
call IssueTargetOrder(h,"attack",enemy)
endif
endif
else
call IssuePointOrder(h,"attack",x,y)
endif
set enemy=null
return true
endfunction
function CAIEnterRoom takes unit h, integer room returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local boolean ok
local real x=1545.6
local real y=4344.2
if GetHeroLevel(h)<15 or GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)<5000 or CAITime<CAIRoomRetry[pid] then
return false
endif
if room==2 then
set x=4432.9
set y=-1832.2
set ok=CAIBuy(h,'I0AV',5000,0,GetUnitX(gg_unit_n00A_0077),GetUnitY(gg_unit_n00A_0077))
else
set ok=CAIBuy(h,'I0BD',5000,0,GetUnitX(gg_unit_n00A_0077),GetUnitY(gg_unit_n00A_0077))
endif
// Mark entry only after the original pickup trigger actually teleports the hero.
if CAINear(h,x,y,700.) then
set CAIRoom[pid]=room
set CAIRoomStarted[pid]=CAITime
set CAIRoomUntil[pid]=CAITime+60.
elseif CAINear(h,GetUnitX(gg_unit_n00A_0077),GetUnitY(gg_unit_n00A_0077),550.) then
set CAIRoomRetry[pid]=CAITime+15.
endif
return ok
endfunction
function CAIGrow takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local integer gold=GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)
local integer cost=0
local integer reserve=0
local integer targetLevel=IMaxBJ(20,CAITargetWave*3+10)
local boolean result=false
if CAIRoom[pid]>0 then
return CAIFarmRoom(h)
endif
// Finish genuine water deliveries before shopping/room entry.
if CAIHas(h,'bzbe') or CAIHas(h,'bzbf') or CAIWaterDone[pid]<2 then
set CAIMode[pid]="water"
return CAIWater(h)
endif
set cost=CAINextGearCost(h)
if GetHeroLevel(h)>=15 then
set reserve=5000
endif
if GetHeroLevel(h)>=15 and GetHeroLevel(h)<targetLevel and gold>=5000 and CAIReadiness(h)<1. then
set CAIMode[pid]="training room"
return CAIEnterRoom(h,1)
endif
if cost>0 and gold>=cost+reserve then
set CAIMode[pid]="equipment"
return CAIGear(h)
endif
if GetHeroLevel(h)<15 or gold<5000 then
set CAIMode[pid]="water"
return CAIWater(h)
endif
if CAIReadiness(h)<1. then
if gold<IMaxBJ(10000,cost+5000) then
set CAIMode[pid]="gold room"
return CAIEnterRoom(h,2)
else
set CAIMode[pid]="training room"
return CAIEnterRoom(h,1)
endif
endif
set CAIMode[pid]="ready"
return false
endfunction
