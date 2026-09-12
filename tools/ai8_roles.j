function CAI8RoleCast takes unit h, unit target returns boolean
local integer id=GetUnitTypeId(h)
local group g=CreateGroup()
local unit u
local unit ally=null
local boolean ok=false
call GroupEnumUnitsInRange(g,GetUnitX(h),GetUnitY(h),650.,null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if CAIAlive(u) and IsUnitAlly(u,GetOwningPlayer(h)) and IsUnitType(u,UNIT_TYPE_HERO) and GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.8 then
set ally=u
endif
endloop
call DestroyGroup(g)
set g=null
set u=null
if id=='H00Q' and (ally!=null or target!=null) then
if ally==null then
set ally=h
endif
set ok=CAICast(h,ally,'A0JO',"healingward",2)
elseif id=='H046' and (ally!=null or target!=null) then
set ok=CAICast(h,h,'A0U3',"roar",0)
elseif id=='E02L' and target!=null then
if GetWidgetLife(h)<GetUnitState(h,UNIT_STATE_MAX_LIFE)*.6 and GetUnitAbilityLevel(h,'B00H')==0 then
set ok=CAICast(h,h,'A0GJ',"berserk",0)
endif
if not ok and GetUnitAbilityLevel(h,'Bblo')==0 then
set ok=CAICast(h,h,'A0AR',"bloodlust",1)
endif
elseif target!=null and (CAI8CC!=target or CAITime>=CAI8CCUntil) then
if id=='H00O' then
set ok=CAICast(h,target,'A0B0',"firebolt",1)
if not ok then
set ok=CAICast(h,target,'A0GW',"flamestrike",2)
endif
if not ok then
set ok=CAICast(h,target,'A06H',"frostnova",1)
endif
elseif id=='E00L' then
if CAINear(h,GetUnitX(target),GetUnitY(target),350.) then
set ok=CAICast(h,target,'A057',"stomp",0)
endif
if not ok then
set ok=CAICast(h,target,'A04Y',"silence",2)
endif
if not ok then
set ok=CAICast(h,target,'A058',"frostnova",1)
endif
endif
if ok then
set CAI8CC=target
set CAI8CCUntil=CAITime+2.
endif
endif
set ally=null
return ok
endfunction
