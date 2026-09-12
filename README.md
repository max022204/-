# 羈絆 7.3.7 AI 版

Warcraft III 守城地圖的分析、AI 腳本及建置工具。

AI 優先守城，安全時送水、練等、賺錢與購買／升級裝備。預設選取柱間、我愛羅與六道斑；角色已被選取時使用替補。以每波敵軍生命、攻擊與護甲作為成長目標，預設倍率為 AI 能力 × 2.5。

完整分析及使用說明見 [分析報告](output/分析報告/00_閱讀與使用.md)，成長邏輯見 [AI 成長與能力目標](output/分析報告/05_AI成長與能力目標.md)。

## 檔案

- `tools/castle_ai.j`：守城、送水、購裝與技能控制。
- `tools/growth_ai.j`：能力目標、練等房與賺錢房決策。
- `tools/build.py`：將 AI 合併至原地圖並重新封裝。
- `tools/test_growth.py`、`tools/verify.py`：離線決策及封裝驗證。
- `output/`：解析資料、分析報告與離線驗證結果。

原始地圖、產出地圖、解包資源及下載的第三方執行檔不納入 Git。報告中指向這些檔案的連結僅適用於完成建置的本機工作目錄。

## 本機建置

使用 Windows、Python 3、原始 `000羈絆7.3.7.w3x` 及 Warcraft III 安裝資源。將原圖複製為 `output/original.w3x`。從 [StormLib](https://github.com/ladislav-zezula/StormLib) 取得 DLL，放於 `tools/stormlib/x64/StormLib.dll`；從 [pjass](https://github.com/lep/pjass) 取得檢查工具，放於 `tools/pjass.exe`。

在專案根目錄依序執行：

```powershell
python tools/extract.py
python tools/mpq.py
python tools/analyze.py
python tools/inspect_data.py
python tools/objects.py
python tools/build.py
python tools/test_growth.py
python tools/verify.py
python tools/report.py
python tools/update_growth_docs.py
```

部分工具使用本機 Warcraft III 安裝路徑，其他電腦使用前需調整。建置產物為 `output/000_Bonds737_AI3.w3x`，安裝時可命名為 `000羈絆7.3.7_AI版_三人守城.w3x`。

目前完成靜態分析、腳本語法與離線決策檢查；尚未在遊戲內完整驗證或通關。原圖需要的 DzAPI、EX、YDWE 等擴展環境仍須具備。AI 尚未涵蓋所有進階任務。
