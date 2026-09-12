// AI6: defense always preempts work; wave readiness is display-only.
function CAIWantDefense takes real remaining returns boolean
return CAIWaveActive or (udg_boshu>0 and remaining>0. and remaining<=8.)
endfunction
function CAIAllowGrowth takes integer pid returns boolean
return not CAIHold and CAIQuiet[pid]>=2.
endfunction
function CAIMoveOrder takes unit h, string order, real x, real y returns nothing
local integer pid=GetPlayerId(GetOwningPlayer(h))
if CAIOrderUnit[pid]!=h or GetUnitCurrentOrder(h)!=OrderId(order) or CAIOrderX[pid]!=x or CAIOrderY[pid]!=y then
call IssuePointOrder(h,order,x,y)
set CAIOrderUnit[pid]=h
set CAIOrderX[pid]=x
set CAIOrderY[pid]=y
endif
endfunction
function CAIAttackOrder takes unit h, unit enemy returns nothing
local integer pid=GetPlayerId(GetOwningPlayer(h))
if GetUnitCurrentOrder(h)!=OrderId("attack") or CAIAttackTarget[pid]!=enemy then
call IssueTargetOrder(h,"attack",enemy)
set CAIAttackTarget[pid]=enemy
endif
endfunction
function CAIGrow takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local integer gold=GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)
local integer cost=0
local integer reserve=0
local boolean result=false
if CAIMirrorSlot[pid]>0 then
return CAIFightMirror(h)
endif
if CAIRoom[pid]>0 then
if (CAIRoom[pid]==1 and CAINear(h,1545.6,4344.2,900.)) or (CAIRoom[pid]==2 and CAINear(h,4432.9,-1832.2,900.)) then
return CAIFarmRoom(h)
endif
// An original-map teleport or revival invalidates the saved room.
set CAIRoom[pid]=0
endif
if CAIHas(h,'bzbe') or CAIHas(h,'bzbf') or CAIWaterDone[pid]<2 then
set CAIMode[pid]="water"
return CAIWater(h)
endif
// Keep AI5's real-material forging, pet transfers, loot and item-use logic.
if CAIEquipmentDelivery(h) then
set CAIMode[pid]="equipment delivery"
return true
endif
set cost=CAINextGearCost(h)
if GetHeroLevel(h)>=15 then
set reserve=5000
endif
if cost>0 and gold>=cost+reserve and GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_LUMBER)>=CAIPlannedLumber then
set CAIMode[pid]="endgame equipment"
set result=CAIGear(h)
if result then
return true
endif
endif
if GetHeroLevel(h)<15 or gold<5000 then
set CAIMode[pid]="water"
return CAIWater(h)
endif
// Mirror safety/DPS estimation and shared-room reservations remain AI5's rules.
// Affordable final-gear steps are handled before spending time on mirrors.
if CAIEnterMirror(h) then
set CAIMode[pid]="mirror"
return true
endif
if CAITime<CAIRoomRetry[pid] then
set CAIMode[pid]="water (room retry)"
return CAIWater(h)
endif
// Save at least a fusion-stone budget; a completed wave is never a stopping point.
if gold<IMaxBJ(255000,cost+5000) or GetHeroLevel(h)>=10000 then
set CAIMode[pid]="gold for endgame"
return CAIEnterRoom(h,2)
endif
set CAIMode[pid]="continuous training"
return CAIEnterRoom(h,1)
endfunction
