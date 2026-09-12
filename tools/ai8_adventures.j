function CAI8Equipped takes unit h returns boolean
local integer i=0
local integer n=0
loop
exitwhen i>=6
if LoadInteger(CAIEquipment,GetItemTypeId(UnitItemInSlot(h,i)),1)>0 then
set n=n+1
endif
set i=i+1
endloop
return n>=2
endfunction
function CAI8Material takes unit h returns integer
local integer stage=1
local integer slot
loop
exitwhen stage>3
set slot=1
loop
exitwhen slot>3
call CAIRecipeData(CAIPrimary(h),stage,slot)
if CAIRecipeBase!=0 and CAIOwned(h,CAIRecipeBase) and not CAIOwned(h,CAIRecipeResult) and not CAIOwned(h,CAIRecipeGem) then
return stage
endif
set slot=slot+1
endloop
set stage=stage+1
endloop
return 0
endfunction
function CAI8Matches takes integer id, integer tier returns boolean
if tier==1 then
return id=='ngno' or id=='ngnv' or id=='n033' or id=='n032'
elseif tier==2 then
return id=='n02O'
elseif tier==3 then
return id=='n02Y' or id=='n02Z'
elseif tier==4 then
return id=='n03R' or id=='n03S' or id=='n03U' or id=='n03T' or id=='n03V'
endif
return false
endfunction
function CAI8Safe takes unit h, unit e returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
// Require recent damage evidence and withstand several raw enemy hits.
return CAIAlive(e) and CAISampleDPS[pid]>0. and CAITime-CAISampleAt[pid]<60. and CAIWatchSignature[pid]==CAILoadout(h) and GetWidgetLife(e)<CAISampleDPS[pid]*15. and CAIAttack(e)*5.<GetWidgetLife(h)
endfunction
function CAI8Find takes unit h, integer tier returns unit
local group g=CreateGroup()
local unit u
local unit best=null
local real distance=1000000000.
local real d
call GroupEnumUnitsOfPlayer(g,Player(PLAYER_NEUTRAL_AGGRESSIVE),null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if CAI8Matches(GetUnitTypeId(u),tier) and not IsUnitHidden(u) and GetUnitAbilityLevel(u,'Avul')==0 and CAI8Safe(h,u) then
set d=(GetUnitX(h)-GetUnitX(u))*(GetUnitX(h)-GetUnitX(u))+(GetUnitY(h)-GetUnitY(u))*(GetUnitY(h)-GetUnitY(u))
if d<distance then
set distance=d
set best=u
endif
endif
endloop
call DestroyGroup(g)
set g=null
set u=null
return best
endfunction
function CAI8BeachOpen takes nothing returns boolean
return LoadInteger(YDHT,GetHandleId(Player(PLAYER_NEUTRAL_PASSIVE)),$FAF23837)>=1
endfunction
function CAI8Return takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
if CAIRecall(h) then
return true
endif
call CAIMoveOrder(h,"move",GetUnitX(gg_unit_hcas_0007),GetUnitY(gg_unit_hcas_0007))
if CAINear(h,GetUnitX(gg_unit_hcas_0007),GetUnitY(gg_unit_hcas_0007),1200.) then
set CAI8TripKind[pid]=0
set CAI8Target[pid]=null
set CAI8Retry[pid]=CAITime+15.
endif
return true
endfunction
function CAI8Trip takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local unit e=CAI8Target[pid]
local boolean ok=false
if CAITime>=CAI8Until[pid] or GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.4 or (CAI8TripKind[pid]==2 and not CAI8BeachOpen()) then
set ok=CAI8Return(h)
set e=null
return true
endif
if CAI8TripKind[pid]==2 and CAI8Step[pid]<2 then
if CAI8Step[pid]==0 then
set ok=CAIBuy(h,'I06L',3500,0,GetUnitX(gg_unit_n00A_0077),GetUnitY(gg_unit_n00A_0077))
if CAINear(h,27.6,-4359.9,700.) then
set CAI8Step[pid]=1
endif
else
set ok=CAIBuy(h,'I0D0',0,0,GetUnitX(gg_unit_n00R_0010),GetUnitY(gg_unit_n00R_0010))
if RectContainsUnit(gg_rct______________031,h) then
set CAI8Step[pid]=2
set CAI8Until[pid]=CAITime+90.
endif
endif
set e=null
return true
endif
if not CAIAlive(e) then
if CAI8LootUntil[pid]==0. then
set CAI8LootUntil[pid]=CAITime+6.
endif
call CAILootEquipment(h)
if CAITime>=CAI8LootUntil[pid] then
set ok=CAI8Return(h)
endif
set e=null
return true
endif
if CAINear(h,GetUnitX(e),GetUnitY(e),850.) then
if CAITime-CAI8Progress[pid]>8. and GetWidgetLife(e)>=CAI8LastHP[pid] then
set ok=CAI8Return(h)
elseif CAIAttack(e)*3.>GetWidgetLife(h) then
set ok=CAI8Return(h)
else
if GetWidgetLife(e)<CAI8LastHP[pid] then
set CAI8Progress[pid]=CAITime
endif
set CAI8LastHP[pid]=GetWidgetLife(e)
set ok=CAISpells(h,e)
if not ok then
call CAIAttackOrder(h,e)
endif
endif
else
set CAI8Progress[pid]=CAITime
call CAIMoveOrder(h,"move",GetUnitX(e),GetUnitY(e))
endif
set e=null
return true
endfunction
function CAI8StartTrip takes unit h returns boolean
local integer pid=GetPlayerId(GetOwningPlayer(h))
local integer tier=CAI8Material(h)
local integer kind=1
local unit e=null
if CAITime<CAI8Retry[pid] or not CAIOpeningDone[pid] or not CAI8Equipped(h) or not CAIHGConditions(GetOwningPlayer(h)) or GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.85 then
return false
endif
if CAI8BeachOpen() and GetPlayerState(GetOwningPlayer(h),PLAYER_STATE_RESOURCE_GOLD)>=8500 then
set e=CAI8Find(h,4)
if e!=null then
set kind=2
endif
endif
if e==null and tier>0 then
set e=CAI8Find(h,tier)
endif
if e==null then
set CAI8Retry[pid]=CAITime+10.
return false
endif
set CAI8TripKind[pid]=kind
set CAI8Step[pid]=0
set CAI8Until[pid]=CAITime+60.
set CAI8Target[pid]=e
set CAI8LastHP[pid]=GetWidgetLife(e)
set CAI8Progress[pid]=CAITime
set CAI8LootUntil[pid]=0.
set CAIMode[pid]="material hunt"
if kind==2 then
set CAIMode[pid]="beach event via mentor / U9"
endif
set e=null
return CAI8Trip(h)
endfunction
