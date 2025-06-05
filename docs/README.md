# 會議記錄優化與評估系統

## 專案概述

本專案是一個基於大型語言模型（LLM）的會議記錄優化與評估系統。系統具備疊代優化引擎、多種策略組合、自動評估機制等功能，專注於提升中文會議記錄的品質與可讀性。

### 核心特點

- 🚀 **智能優化**：30種優化策略，涵蓋角色、結構、內容、格式、語言、品質六大維度
- 🔄 **疊代優化**：自動化疊代優化引擎，支援 early stopping
- 📊 **多維度評估**：整合 BERTScore、ROUGE、結構化程度等多項指標
- 🎯 **策略管理**：智能策略組合與自動調整機制
- 🤖 **語意分段**：基於 LLM 的智能語意分段功能
- 📈 **效能追蹤**：完整的效能監控與報告系統

## 系統需求

- Python 3.8+
- 作業系統：macOS/Linux/Windows
- [Ollama](https://ollama.com/) 本地 LLM 服務
- 建議記憶體：16GB+
- 建議硬碟空間：20GB+

## 快速開始

### 1. 安裝

```bash
# 克隆專案
git clone https://github.com/colabbrave/exam08.git
cd exam08

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r config/requirements.txt
```

### 2. 下載模型

```bash
# 下載基礎模型
ollama pull gemma3:4b

# 下載優化模型（可選）
ollama pull gemma3:12b
```

### 3. 開發環境設定

```bash
# 安裝開發工具
pip install -r config/requirements-dev.txt

# 設定 pre-commit hooks
pre-commit install
```

## 專案結構

```
exam08/
├── src/                    # 原始碼
│   ├── analyze/           # 分析相關模組
│   ├── optimize/          # 優化相關模組
│   └── utils/             # 工具函式
├── tests/                 # 測試
│   ├── unit/             # 單元測試
│   └── integration/      # 整合測試
├── docs/                  # 文件
│   ├── guides/           # 使用指南
│   └── reports/          # 報告文件
├── config/               # 設定檔
│   ├── models/          # 模型設定
│   └── strategies/      # 策略設定
├── data/                 # 資料
│   ├── raw/             # 原始資料
│   └── processed/       # 處理後資料
├── output/              # 輸出
│   ├── results/         # 結果
│   └── logs/           # 日誌
├── assets/              # 靜態資源
└── scripts/             # 腳本
```

## 使用指南

### 基本使用

```bash
# 單檔優化
python src/optimize/optimizer.py "data/raw/meeting.txt" --max-iterations 2

# 批次優化
./scripts/run_optimization.sh

# 評估結果
python src/analyze/evaluate.py
```

### 進階功能

1. **語意分段**
   ```bash
   ENABLE_SEMANTIC_SEGMENTATION=true ./scripts/run_optimization.sh --semantic-model gemma3:12b
   ```

2. **自訂策略**
   - 編輯 `config/strategies/strategy_config.json`
   - 參考 `docs/guides/STRATEGY_GUIDE.md`

3. **效能監控**
   - 查看 `output/logs/optimization.log`
   - 分析 `output/results/performance_report.json`

## 開發規範

### 1. 命名規則

- **檔案名稱**：小寫字母，用底線分隔
  ```python
  analyze_meeting.py
  optimize_content.py
  ```

- **類別名稱**：大寫開頭
  ```python
  class MeetingAnalyzer:
  class ContentOptimizer:
  ```

- **函式名稱**：小寫字母，用底線分隔
  ```python
  def process_meeting():
  def evaluate_quality():
  ```

- **變數名稱**：小寫字母，用底線分隔
  ```python
  meeting_data = {}
  quality_score = 0.95
  ```

### 2. 程式碼風格

- 使用 Black 進行格式化
  ```bash
  black src/ tests/
  ```

- 使用 Flake8 進行程式碼檢查
  ```bash
  flake8 src/ tests/
  ```

- 使用 isort 排序 import
  ```bash
  isort src/ tests/
  ```

### 3. 測試規範

- 單元測試覆蓋率 > 80%
  ```bash
  pytest --cov=src tests/
  ```

- 整合測試涵蓋主要功能
  ```bash
  pytest tests/integration/
  ```

## 效能指標

### 最佳表現

- **整體分數**：0.5529
- **語義相似度**：0.6771
- **內容涵蓋度**：0.1478
- **結構品質**：0.8500

### 策略效能排行

1. 明確標註發言者 (0.5529)
2. 精簡冗詞 (0.5497)
3. 專業術語標準化 (0.5446)
4. 專業角色定義 (0.5429)
5. 明確標示決議事項 (0.5416)

## 常見問題

1. **模型載入失敗**
   - 確認 Ollama 服務是否運行
   - 檢查模型是否正確下載

2. **記憶體不足**
   - 使用較小的模型（如 gemma3:4b）
   - 調整批次大小

3. **效能問題**
   - 檢查 `config/models/model_config.json`
   - 調整優化參數

## 貢獻指南

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 發起 Pull Request

## 授權

MIT License

## 聯絡方式

- 專案維護者：[Your Name]
- 電子郵件：[your.email@example.com]
- GitHub：[your-github-profile]
