import json,re,hashlib
from pathlib import Path
OUT=Path('output');REPORT=OUT/'分析報告';REPORT.mkdir(exist_ok=True)
def load(n):return json.loads((OUT/(n+'.json')).read_text('utf-8'))
u=load('units');a=load('abilities');it=load('items');w=load('waves');up=load('upgrades');changes=load('ability_overrides')
j=Path('extracted/war3map.j').read_text('utf-8',errors='replace')
def clean(s):return re.sub(r'\|[cC][0-9a-fA-F]{8}|\|[rR]','',str(s)).replace('|n','；').strip('"').replace('|','／').replace('\n','；')
def nm(v):return clean(v.get('Propernames',v.get('Name','')))
def f(v,k):return v.get(k,'0')
def num(v,k):
 try:return float(v.get(k,0))
 except:return 0
def damage(v):
 b=num(v,'dmgplus1');d=num(v,'dice1');s=num(v,'sides1');return f'{b+d:g}～{b+d*s:g}'
def raw(h):return bytes.fromhex(h).decode('latin1')
functions=[]
for m in re.finditer(r'^function (\w+).*?^endfunction',j,re.M|re.S):functions.append({'name':m[1],'line':j.count('\n',0,m.start())+1,'body':m[0]})
def refs(id):
 h=id.encode('latin1').hex().upper()
 return [(x['name'],x['line']) for x in functions if '$'+h in x['body']]
def link(line):return f'../../extracted/war3map.j:{line}'
def sources(id):return '、'.join(f'[{name}]({link(line)})' for name,line in refs(id)[:12]) or '未找到直接 rawcode 引用；可能由陣列或通用流程處理。'
def write(n,lines):(REPORT/n).write_text('\n'.join(lines)+'\n','utf-8-sig')
roster={int(n):raw(h) for n,h in re.findall(r'set udg_Yx_Lxing\[(\d+)\]=\$([0-9A-F]{8})',j)}
for id,obj in changes.items():
 for change in obj['changes']:
  mapping={'acdn':'Cool','amcs':'Cost','aran':'Rng','aare':'Area','adur':'Dur','ahdu':'HeroDur'}
  if change['field'] in mapping:a.setdefault(id,{})[mapping[change['field']]+str(change['level'])]=str(change['value'])
def aval(v,key,level):
 return v.get(key+str(level),v.get(key+str(min(level,4)),v.get(key+'1','未提供')))
boss={}
for arr in ['udg_Boss_B','udg_Boos_C','udg_BOSS_xiao']:
 boss[arr]={int(n):raw(h) for n,h in re.findall(r'set '+arr+r'\[(\d+)\]=\$([0-9A-F]{8})',j)}
lines=['# 30 波敵軍與動態加成','', '資料取自這一份地圖的 SLK 與 war3map.j。以下為物件基礎值，沒有把難度科技、光環、BUFF 或腳本改值混入；普攻範圍包含傷害骰。英雄型 BOSS 另外受到英雄等級與三圍影響。','', '|波|兵種／ID|生命|普攻|護甲／類型|攻擊類型|間隔秒|射程|移速|技能|','|---|---|---:|---:|---|---|---:|---:|---:|---|']
for n,id in w.items():
 v=u[id];abs=', '.join(clean(a.get(k,{}).get('Name',k))+'('+k+')' for k in v.get('abilList','').split(',') if k and k!='_') or '無'
 lines.append(f'|{n}|{nm(v)} `{id}`|{f(v,"HP")}|{damage(v)}|{f(v,"def")}／{f(v,"defType")}|{f(v,"atkType1")}|{f(v,"cool1")}|{f(v,"rangeN1")}|{f(v,"spd")}|{abs}|')
lines+=['','## 出兵節奏與數量','','每波以 1.5 秒為週期執行 40 次。第 1 次先隨機出小頭目（1 或 2 隻，各 50%）；第 2～40 次，每次三路各 1 隻普通兵，所以每波正常兵為 117 隻。第 40 次後進入下一波倒數。一般倒數 100 秒；第 15、24 波為 125 秒，高手模式為 150 秒。','',f'來源：[Trig_Chubin006Actions]({link(next(x["line"] for x in functions if x["name"]=="Trig_Chubin006Actions"))})、[Trig_Chubin001Actions]({link(next(x["line"] for x in functions if x["name"]=="Trig_Chubin001Actions"))})。','','## 固定 BOSS','','|波|等級|主 BOSS|同行 BOSS|','|---|---:|---|---|']
for idx,n in enumerate([4,8,12,15,20,24,27,30],1):
 b=boss['udg_Boss_B'].get(idx);c=boss['udg_Boos_C'].get(idx) if n not in [15,24] else None
 lines.append(f'|{n}|{n*2}|{nm(u.get(b,{}))} `{b}`|{nm(u.get(c,{})) if c else "無一般同行 BOSS"} {"`"+c+"`" if c else ""}{"；另加 "+nm(u.get("E05T",{}))+" `E05T`" if n==30 else ""}|')
lines+=['','小頭目池：'+ '、'.join(nm(u.get(id,{}))+' `'+id+'`' for id in boss['udg_BOSS_xiao'].values())+'；等級＝波次×2。技能 A04M 若存在，會同步設為波次等級。','','偷襲每次兩處各出 10 隻（共 20）；前 29 波使用下一波普通兵，第 30 波改用 n03D。注意原腳本條件沒有把所有 `or` 包進難度條件，因此 13／17／22／27 等波會不受前面的 udg_touxizs==1 限制；分析與修改沒有擅自修正原圖的這項行為。','','## 難度科技','','所有 30 波普通兵的 upgrades 為 R001,R006；R005 的波次增長不可直接套到不具 R005 的普通兵身上。下表列出難度選單設定到 Player(11) 的科技等級，實際受益要再比對單位 upgrades 欄位。','','|難度|R001|R002|','|---|---:|---:|']
diffbody=next(x['body'] for x in functions if x['name']=='Trig_Nand003Actions')
for block in re.split(r'if GetClickedButtonBJ\(\)==udg_DHKkan\[\d+\] then',diffbody)[1:]:
 name=re.search(r'set udg_DMB_zfc\[1\]="([^"]+)"',block)
 if not name:continue
 levels=[]
 for h in ['52303031','52303032']:
  m=re.search(r'SetPlayerTechResearchedSwap\(\$'+h+r',(\d+),Player\(11\)\)',block);levels.append(m[1] if m else '0')
 lines.append('|'+clean(name[1])+'|'+'|'.join(levels)+'|')
lines+=['','## 科技效果原值','','科技等級 L>0 時，其 base/mod 效果參數通常以 base + mod×(L−1) 表示；ratt、rarm 還需依引擎與單位 dmgUp1、defUp 解讀，不能只把科技數字直接加到面板。此處保留效果碼與原參數，未將未實測的推算冒充實戰數字。','','|科技|效果 1～4（base / 每級增量）|最大等級|','|---|---|---|']
for id,v in up.items():
 if id.startswith('R00'):lines.append('|'+id+'|'+'；'.join(f'{v.get("effect"+str(k),"無")}：{v.get("base"+str(k),"0")} / {v.get("mod"+str(k),"0")}' for k in range(1,5))+'|'+v.get('maxlevel','')+'|')
lines+=['','R005：第 5～12 波每波 +1，第 13～25 波每波 +3，第 26～30 波每波 +4，累積到第 30 波為 67 級；僅適用具有該科技的單位。R00F 另有超神初始與第 7／11／15 波的条件，原圖 `and/or` 優先順序同樣需注意。','','第 24 波：未解救尾獸會提高外道魔像相關生命加成（R00D）；第 27 波：未完成阻止穢土轉生的團隊任務，追加 R00E；第 30 波有額外十尾人柱力階段。','','## 各波單位完整欄位與技能明細']
for n,id in w.items():
 v=u[id];lines+=['',f'### 第 {n} 波：{nm(v)} ({id})','', '```json',json.dumps(v,ensure_ascii=False,indent=2),'```']
 for aid in v.get('abilList','').split(','):
  if aid in a:lines+=['',f'**{clean(a[aid].get("Name",aid))} ({aid})**：'+clean(a[aid].get('Ubertip',a[aid].get('Researchubertip','未提供提示文字'))),'',sources(aid)]
lines+=['','## BOSS 基礎資料']
for id in dict.fromkeys([v for d in boss.values() for v in d.values()]+['E05T','n03D']):
 lines+=['',f'### {nm(u.get(id,{}))} ({id})','','```json',json.dumps(u.get(id,{}),ensure_ascii=False,indent=2),'```']
write('01_敵軍30波.md',lines)
lines=['# 全角色與技能','',f'角色註冊陣列有 {len(roster)} 個有效條目（索引上限 57，中間有空缺）；它不等於 57 名可選英雄。選角區還有重複、替代與初始化時移除的模型。下列依實際註冊條目列出；所有單位與變身形態另附 units.json，共 {len(u)} 個物件。','', '英雄生命欄是物件基礎 HP；本圖 StrHitPointBonus=30，因此英雄面板生命還要加力量帶來的生命。技能提示中的公式是作者文字，不保證與觸發器完全一致；每項附上對應程式引用。','','## 守城 AI 組合','','千手柱間：恢復樹、全屬性支援與範圍傷害。木遁之力提示每秒恢復 2% 生命、友軍全屬性 +20×技能等級，適合固定陣地。','','我愛羅：600 基礎射程、智力成長 5.5，砂石雨冷卻 8 秒，提示帶 3 秒暈眩；便於自動施法與清兵。','','六道斑：敏捷成長 4.5、輪墓、扇形攻擊、神樹範圍減速；補足後期輸出。三者組合為靜態資料選型，尚未以所有角色配對進行通關基準測試，不能稱為已證明的唯一最強組合。','','其餘候選以射程及技能中的範圍、控制、恢复、召喚等標記排序，作為角色被占用時的替補。分數是程式選角優先值，非勝率或傷害測量。','','## 隱藏角色','','|ID|實際角色|原限制|修改|','|---|---|---|---|','|H04S|長門|YINc_buff[2]|開局解鎖|','|N024|六道帶土|YINc_buff[1]；訊息誤稱六道仙人|開局解鎖|','|N02F|六道斑|YINc_buff[3]|開局解鎖|','|H046|白蛇仙人兜|YINc_buff[4]|開局解鎖|','','原檔四個聊天觸發器均使用 `GOD`。本修改直接啟用選取旗標，不要求輸入，也保留一般斑與阿飛供選擇。平台活動皮膚、公會或存檔獎勵未改為免費解鎖。']
for idx,id in roster.items():
 v=u[id];lines+=['',f'## {idx}. {nm(v)} `{id}`','',f'主屬性：{v.get("Primary","未提供")}；力量 {f(v,"STR")} / 成長 {f(v,"STRplus")}；敏捷 {f(v,"AGI")} / 成長 {f(v,"AGIplus")}；智力 {f(v,"INT")} / 成長 {f(v,"INTplus")}。',f'基礎 HP {f(v,"HP")}，基礎護甲 {f(v,"def")}，普攻 {damage(v)}，射程 {f(v,"rangeN1")}，間隔 {f(v,"cool1")} 秒，移速 {f(v,"spd")}。','',clean(v.get('Ubertip',''))]
 for aid in v.get('heroAbilList','').split(','):
  av=a.get(aid,{})
  if not av:continue
  levels=int(av.get('levels',1))
  lines+=['',f'### {clean(av.get("Name",aid))} `{aid}`','',clean(av.get('Ubertip',av.get('Researchubertip',''))),'',f'學習等級：{av.get("reqLevel","未提供")}；最高 {levels} 級；原型：{av.get("code","")}。','', '|技能等級|冷卻秒|耗魔|射程|','|---|---:|---:|---:|']
  for level in range(1,levels+1):lines.append(f'|{level}|{aval(av,"Cool",level)}|{aval(av,"Cost",level)}|{aval(av,"Rng",level)}|')
  lines+=['',sources(aid)]
write('02_全角色技能.md',lines)
quests=[(id,v) for id,v in it.items() if any(t in v.get('Name','')+' '+v.get('Description','') for t in ['任务等级','任务 -','接受/提交','提交','挑战','任務'])]
lines=['# 任務與挑戰','',f'下列收錄 {len(quests)} 個相關任務、挑戰或提交物件。任務提示與程式可能不一致，實際觸發條件以所附原腳本為準。','','## AI 已接入的任務','','尋找水源：前往下忍導師 n00A（3968,3520），取得 I03Y 觸發的空瓶 bzbe，步行到水區（1712,-272），由原有進入區域觸發器換成滿瓶 bzbf，再返回導師取得原圖 1000 金幣與 300 經驗。未偽造任務完成旗標或直接加獎勵。','','每次只准一名 AI 離開陣地處理裝備或送水，其他兩名留守；偵測主城周圍 2400 範圍敵軍或城堡生命低於 80% 就停止外務回防。已攜帶的瓶子留到下次安全時續作。大型團隊任務、尾獸、仙人重數與副本的自主求解尚未實作，這不是全任務自動通關 AI。','','## 全任務／挑戰物件']
for id,v in quests:lines+=['',f'### {clean(v.get("Name",id))} `{id}`','',clean(v.get('Ubertip',v.get('Description',''))),'',f'物件價格：金幣 {f(v,"goldcost")}、木材 {f(v,"lumbercost")}。部分價格由觸發器另扣，不能只看商店標價。','',sources(id)]
lines+=['','## 團隊任務與任務系統程式索引','']
for x in functions:
 if (re.search(r'function (Trig_Renwu|Trig_Tuan|Trig_XL)',x['body']) or ('任务' in x['body'] and 'Actions' in x['name'])) and not x['name'].startswith('Init'):
  messages=re.findall(r'"([^"\n]*(?:任务|奖励|完成|等级)[^"\n]*)"',x['body'])
  lines.append(f'- [{x["name"]}，原腳本第 {x["line"]} 行]({link(x["line"])})：'+ '；'.join(clean(t) for t in messages[:3]))
write('03_任務與挑戰.md',lines)
lines=['# 全物品與裝備','',f'共 {len(it)} 個物件，包含裝備、藥品、任務憑證、合成按鈕、挑戰入口；不是每個物件都能裝備。物品提示是作者設定，並附有 rawcode 的腳本引用。價格 0 可能代表觸發器另扣成本。','','## AI 裝備路線','','護腕 1000、護靴 2000、護額 1000 → 各使用 3000 金幣升級憑證四次 → 三件影級物品 + 22000 合成憑證 → 影之玉 +0。合計 62000 金幣。','','忍者鎧甲 3000 → 每次 3000，五次升級至龍鱗鎧甲（合計 18000）。近戰角色另購雷神之劍 13000，四次每次 3000 升級至真雷神劍（合計 25000）；智力角色增加魔法垂飾 200。','','影之玉强化使用原圖 I0A8 觸發器扣款：+0→+1 實際為 70000，之後每級多 10000，至 +15；物品文字寫「每次消耗60000」與初次實際條件不一致。最高只按原圖支持上限執行。','','AI 不會無材料產生仙人套裝或專屬神器；高階套裝、材料掉落與其他合成的全部資料保留在下方供查閱。']
for id,v in it.items():
 sellers=[nm(uv)+' `'+uid+'`' for uid,uv in u.items() if id in uv.get('Sellitems','').split(',')]
 lines+=['',f'## {clean(v.get("Name",id))} `{id}`','',f'金幣 {f(v,"goldcost")}；木材 {f(v,"lumbercost")}；類型 {v.get("class","")}；技能 {v.get("abilList","")}。','',clean(v.get('Ubertip',v.get('Description',''))),'','出售者：'+('、'.join(sellers) or '未列於靜態商店清單；檢查掉落、動態出售或合成。'),'',sources(id)]
write('04_全裝備與合成.md',lines)
write('00_閱讀與使用.md',['# 羈絆 7.3.7 地圖分析與 AI 修改版','', '修改地圖：[000_Bonds737_AI3.w3x](../000_Bonds737_AI3.w3x)。原檔完整副本：[original.w3x](../original.w3x)。','', '本次完成静態解析、AI 腳本、重新封裝與離線驗證；尚未在 Warcraft III 內載入及完整通關驗證。這份地圖應視為待實機驗證版本。','', '## 使用方式','','1. 將修改地圖放到 Warcraft III 的 Maps 資料夾，以自訂遊戲開啟。','2. 玩家 8、9、10 預設為電腦；請在大廳確認三格已啟用。AI 只接管前十個友方位置中前三個正在遊戲的電腦玩家，其他人類位置不受控制。','3. 選擇模式與難度；選角啟用後 AI 自動選取柱間、我愛羅、六道斑。角色被選走時，從其餘候選挑選替補。','4. 四名隱藏角色開局可直接雙擊選取，不需要 GOD。','5. `-ai status` 查看 AI 英雄和等級；`-ai hold` 禁止外務、集中守城；`-ai auto` 恢復外務。','', '## 報告','','- [30 波與 BOSS、難度科技](01_敵軍30波.md)','- [全角色、技能、角色選型](02_全角色技能.md)','- [任務條件、獎勵、程式索引](03_任務與挑戰.md)','- [469 物品、商店、升級與合成](04_全裝備與合成.md)','', '完整機器可讀資料：上層目錄 units.json、items.json、abilities.json、ability_overrides.json、upgrades.json、ai_ranking.json。所有 723 個單位物件包含 NPC、召喚物、BOSS 及變身形態，不能當成可選角色數。','', '## 實作範圍與限制','','AI 以防守優先，半秒檢查一次；輪替一人外務，其他兩人留守。正常擊殺及送水取得等級與資源，技能依原圖學習規則，死亡復活沿用原圖。裝備使用原價交易與原有拾取觸發器；安全空檔才離開。沒有保證高難度通關，沒有實作全部團隊／仙人／尾獸任務的自主解法。','', '原圖使用 DzAPI、EX、YDWE 等擴展，原檔可正常運行的遊戲環境仍是必要條件。語法檢查不是擴展相容性或遊戲內效果驗證。','', '工具來源：[StormLib](https://github.com/ladislav-zezula/StormLib)、[pjass](https://github.com/lep/pjass)。遊戲分析資料全部來自使用者提供的本地地圖。'])
print('Reports:',[(p.name,p.stat().st_size) for p in REPORT.iterdir()])
