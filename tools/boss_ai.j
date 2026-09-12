// Two burst specialists supplement the three original castle defenders.
function CAIRoleRank takes integer pid, integer id returns integer
if not CAIBossRole[pid] then
return CAIRank(id)
endif
if id=='E020' then
return 1200
elseif id=='E06N' then
return 1199
elseif id=='E05A' then
return 1100
elseif id=='E048' then
return 1099
elseif id=='H00Q' or id=='H00O' or id=='N02F' then
return 1
endif
return CAIRank(id)
endfunction
function CAIMainBoss takes unit u returns boolean
local integer i=1
local integer id=GetUnitTypeId(u)
loop
exitwhen i>8
if id==udg_BOSS_A[i] then
return true
endif
set i=i+1
endloop
return false
endfunction
function CAIFindBoss takes unit h, real x, real y returns unit
local group g=CreateGroup()
local unit u
local unit best=null
local real score
local real distance=1000000000.
call GroupEnumUnitsInRange(g,x,y,3200.,null)
loop
set u=FirstOfGroup(g)
exitwhen u==null
call GroupRemoveUnit(g,u)
if CAIAlive(u) and IsUnitEnemy(u,GetOwningPlayer(h)) and GetOwningPlayer(u)==Player(11) and not IsUnitHidden(u) and GetUnitAbilityLevel(u,'Aloc')==0 and GetUnitAbilityLevel(u,'Avul')==0 and not IsUnitType(u,UNIT_TYPE_STRUCTURE) and (IsUnitType(u,UNIT_TYPE_HERO) or CAIMainBoss(u)) then
set score=(GetUnitX(u)-x)*(GetUnitX(u)-x)+(GetUnitY(u)-y)*(GetUnitY(u)-y)
if CAIMainBoss(u) then
set score=score-100000000.
endif
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
