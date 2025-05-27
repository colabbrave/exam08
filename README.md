# 會議記錄優化與評估系統

## 專案概述

本專案旨在利用大型語言模型（LLM）來自動優化會議記錄，提高其結構化程度、完整性和可讀性。系統支援多種優化策略，並提供全面的評估框架來衡量優化效果。

## 主要功能

- **多策略優化**：支援多種會議記錄優化策略
- **多模型支援**：可與多種開源和商業語言模型整合
- **自動化評估**：提供多種評估指標來衡量優化效果
- **可擴展架構**：易於添加新的優化策略和評估指標

## 快速開始

### 前置需求
- Python 3.8+
- Ollama 服務 (用於運行本地模型)

### 安裝步驟

```bash
# 1. 克隆存儲庫
git clone https://github.com/colabbrave/exam08.git
cd exam08

# 2. 創建並啟動虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
# .\venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 下載並啟動 Ollama 模型
ollama pull gemma3:4b  # 或其他支援的模型
```

### 基本用法

```bash
# 優化會議記錄
./run_optimization.sh

# 或指定模型
./run_optimization.sh --model gemma3:4b

# 評估優化結果
python scripts/evaluate.py --model gemma3_4b
```

## 專案結構

```
.
├── config/                  # 配置文件
├── data/                    # 數據目錄
│   ├── reference/           # 參考會議記錄
│   └── transcript/          # 原始逐字稿
├── docu/                    # 文檔
├── logs/                    # 運行日誌
├── models/                  # 模型文件
├── prompts/                 # 提示詞模板
│   ├── base/                # 基礎提示詞
│   ├── components/          # 提示詞組件
│   ├── optimized/           # 優化後的提示詞
│   └── preloaded/           # 預加載的提示詞
├── results/                 # 結果輸出
│   ├── evaluation_reports/  # 評估報告
│   └── optimized/           # 優化後的會議記錄
└── scripts/                 # 腳本文件
    ├── evaluate.py          # 評估腳本
    ├── optimize.py          # 優化腳本
    ├── model_manager.py     # 模型管理
    ├── ollama_manager.py    # Ollama 集成
    └── select_model.py      # 模型選擇
```

## 評估結果

### 多指標評估系統

我們實現了全面的多指標評估系統，包含以下主要指標：

#### 1. 語義相似度 (權重 50%)
- **BERTScore F1**：衡量優化前後文本的語義相似度
- **平均分數**：0.85

#### 2. 內容覆蓋度 (權重 30%)
- **ROUGE-1**：unigram 層面的覆蓋度
- **ROUGE-2**：bigram 層面的覆蓋度
- **ROUGE-L**：最長公共子序列
- **平均分數**：0.78

#### 3. 結構化程度 (權重 20%)
- 章節標題質量
- 段落結構質量
- 列表使用適當性
- **平均分數**：0.82

### 模型表現比較

| 模型 | 綜合得分 | 響應時間 | BERTScore | ROUGE-L |
|------|---------|---------|-----------|---------|
| gemma3:4b | 0.85 | 45.2s | 0.88 | 0.75 |
| llama3-8b | 0.82 | 68.7s | 0.86 | 0.73 |
| mistral-7b | 0.80 | 52.1s | 0.84 | 0.72 |

### 最佳實踐策略排名

1. **補充省略資訊** (0.92)
   - 提升內容完整性
   - 自動補全會議中的隱含資訊

2. **明確標註發言者** (0.89)
   - 提高可讀性
   - 便於追蹤討論脈絡

3. **結構化摘要** (0.88)
   - 提升文件結構化程度
   - 便於快速瀏覽重點

4. **專業術語標準化** (0.86)
   - 統一專業術語使用
   - 提高專業性

5. **標準格式模板** (0.85)
   - 確保格式一致性
   - 符合企業規範

> **注意**：詳細評估報告請參考 [評估報告目錄](results/evaluation_reports/)

## 貢獻指南

我們歡迎任何形式的貢獻！以下是參與項目的步驟：

1. Fork 本項目
2. 創建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 代碼風格
- 使用 [Black](https://github.com/psf/black) 進行代碼格式化
- 使用 [Google 風格的 Python 文檔字符串](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

### 提交信息規範
請遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範：
- feat: 新功能
- fix: 修復 bug
- docs: 文檔更新
- style: 代碼格式
- refactor: 代碼重構
- test: 測試相關
- chore: 構建過程或輔助工具的變動

## 專案進度

### 完成情況

1. **基本架構建立** ✅ 已完成
   - 專案目錄結構
   - 基礎優化流程
   - 多模型支援

2. **評估系統實現** ✅ 已完成
   - ✅ 基本評估框架
   - ✅ BERTScore 實現
   - ✅ ROUGE 實現
   - ✅ 多指標整合
   - ✅ 評估報告生成
   - ⏳ 評估報告可視化 (進行中)

### 後續計劃

3. **提示工程優化** 🔜 下一階段
   - 提示詞模板重構
   - 動態範例載入
   - 思維鏈提示

4. **效能優化** ⏳ 未開始
   - 並行處理
   - 快取機制
   - 資源監控

5. **文檔與部署** ⏳ 未開始
   - 使用文檔
   - API 文檔
   - 部署指南

## 最近更新

### 2025-05-28 (最新)
- 完成多指標評估系統整合
- 實現評估報告自動生成功能
- 優化評估指標權重配置
- 更新評估結果文檔
- 改進模型性能追蹤

### 2025-05-27
- 更新 README 文件，改進文檔結構和內容完整性
- 修復評估階段文件路徑比對問題
- 優化模型名稱處理邏輯，支援不同格式的模型名稱
- 改進評估腳本，可選擇性評估特定模型的結果
- 更新 `run_optimization.sh` 腳本，確保正確傳遞模型參數
- 改進錯誤處理和日誌記錄
- 新增模型執行時間統計功能
- 新增策略執行時間統計功能
- 添加 `run_all_models.sh` 腳本用於批量運行多個模型

### 2025-05-27
- 新增模型執行時間統計功能
- 新增策略執行時間統計功能
- 改進模型名稱處理邏輯
- 優化錯誤處理和重試機制
- 添加 `run_all_models.sh` 腳本用於批量運行多個模型

### 2025-05-26
- 實現模型響應時間追蹤
- 優化模型調用過程中的錯誤處理
- 改進重試機制，提高穩定性

### 2025-05-25
- 修復 `time` 模組導入問題
- 修正 `model_timings` 和 `strategy_timings` 變數作用域問題
- 更新評估結果和改進策略

## 授權

本項目採用 [MIT 許可證](LICENSE) 授權。
