# 羈絆 7.3.7 AI 版

最新為 **AI6 五人版**，以使用者正在遊玩的 `000_Bonds737_AI5.w3x` 為基底修正。

- 原三名守城：柱間、我愛羅、六道斑。
- 新增兩名 BOSS 爆發：邁特凱、飛段；優先攻擊進攻主城的 BOSS，普通兵保留大招。
- 有敵軍先防守，清場後五人持續賺錢、練等、升級及合成；波次能力達標不再停工。
- 保留 AI5 裝備路線、寶寶代管、實際材料合成、強化、融合與鏡像挑戰。最終裝備仍需原圖材料、稱號與任務條件。

詳見 [AI6 五人守城與 BOSS 更新](output/分析報告/06_AI6五人守城與BOSS.md) 及 [完整地圖分析索引](output/分析報告/00_閱讀與使用.md)。目前完成離線驗證，尚未遊戲內完整通關測試。

## 建置 AI6

使用 Windows、Python 3，並準備使用者自己的 AI5 地圖。從 [StormLib](https://github.com/ladislav-zezula/StormLib) 取得 DLL，放至 `tools/stormlib/x64/StormLib.dll`；從 [pjass](https://github.com/lep/pjass) 取得檢查工具放至 `tools/pjass.exe`。

```powershell
python tools/build_continuous.py --base "C:/Program Files (x86)/War3 v1.29c/Maps/000_Bonds737_AI5.w3x"
python tools/test_ai6.py
python tools/verify_ai6.py
```

產出 `output/000_Bonds737_AI6.w3x`。遊戲安裝檔名為 `000羈絆7.3.7_AI版_五人守城.w3x`，預設玩家 6～10 為電腦，玩家 1～5 可供人類使用。

驗證工具另需原始地圖副本 `output/original.w3x`、`extracted/Scripts_common.j`、`extracted/Scripts_Blizzard.j` 及原先的解析資料。其他電腦使用時需調整驗證工具中的本機地圖路徑。AI5 的來源雜湊記錄在 `output/continuous_build_manifest.json`；同一路徑改成不同版本時，建置工具會要求先核對備份。

## 主要程式

- `tools/build_continuous.py`：針對 AI5 修改指定函式，保留其他函式與資源。
- `tools/continuous_ai.j`：持續成長與防守優先規則。
- `tools/boss_ai.j`：角色分工與 BOSS 集火優先序。
- `tools/test_ai6.py`：執行實際 JASS 決策的離線情境測試。
- `tools/verify_ai6.py`：封裝、來源完整性、原有函式與語法驗證。

`tools/build.py`、`castle_ai.j`、`growth_ai.j` 等是先前 AI3 版本的建置工具，保留供歷史分析。最新 AI6 使用上面的建置指令。

原始／修改地圖、解包資源、備份與第三方執行檔保留本機，不納入 Git。報告中指向這些檔案的連結需本機資料才能開啟。
