# 提示詞練習重啟專案

這是一個用於優化和評估提示詞的專案，主要用於改進會議記錄的品質。

## 功能特點

- 提示詞優化：使用多種策略優化提示詞
- 會議記錄生成：自動生成結構化的會議記錄
- 品質評估：使用多種指標評估生成結果
- 效能監控：監控系統資源使用情況

## 系統需求

- Python 3.8 或更高版本
- CUDA 支援（建議用於 GPU 加速）

## 安裝步驟

1. 克隆專案：

   ```bash
   git clone [專案網址]
   cd exam08_提示詞練習重啟
   ```

2. 建立虛擬環境：

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate  # Windows
   ```

3. 安裝依賴：

   ```bash
   make install
   ```

## 使用方法

1. 基本使用：

   ```bash
   python scripts/run_semantic_processing.py --input [輸入檔案] --output [輸出目錄]
   ```

2. 優化會議記錄：

   ```bash
   python scripts/optimize_meeting_minutes.py --input [會議記錄] --output [優化後檔案]
   ```

3. 執行測試：

   ```bash
   make test
   ```

## 專案結構

```text
exam08/
├── src/                    # 原始碼
│   ├── analyze/           # 分析相關模組
│   ├── optimize/          # 優化相關模組
│   └── utils/             # 工具函式
├── tests/                  # 測試
│   ├── unit/              # 單元測試
│   └── integration/       # 整合測試
├── docs/                   # 文件
├── config/                 # 設定檔
├── data/                   # 資料
│   ├── raw/               # 原始資料
│   └── processed/         # 處理後資料
├── output/                 # 輸出
│   ├── results/           # 結果
│   └── logs/              # 日誌
└── scripts/                # 腳本
```

## 開發指南

1. 程式碼風格：
   - 使用 Black 進行程式碼格式化
   - 使用 isort 進行 import 排序
   - 使用 Flake8 進行程式碼檢查
   - 使用 MyPy 進行型別檢查

2. 提交規範：
   - 使用 pre-commit hooks 確保程式碼品質
   - 遵循 Git commit 訊息規範

3. 測試規範：
   - 撰寫單元測試和整合測試
   - 確保測試覆蓋率

## 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 文件。

MIT 授權條款允許您：

- 自由使用、修改和分發本專案
- 用於商業和非商業目的
- 在保留原始授權聲明的情況下進行修改

## 貢獻指南

我們歡迎各種形式的貢獻，包括但不限於：

1. 提交問題報告
   - 使用 GitHub Issues 提交問題
   - 清楚描述問題和重現步驟
   - 提供相關的錯誤訊息和環境資訊

2. 提交功能建議
   - 說明新功能的用途和價值
   - 提供可能的實現方案
   - 討論與現有功能的整合方式

3. 提交程式碼
   - 遵循現有的程式碼風格
   - 添加適當的測試
   - 更新相關文件
   - 確保所有測試通過

4. 改進文件
   - 修正錯誤或過時的資訊
   - 改進文件的可讀性
   - 添加使用範例和說明

5. 審查程式碼
   - 檢查程式碼品質
   - 提供建設性的意見
   - 確保符合專案標準

## 效能基準與最佳分數

本專案針對市政會議逐字稿自動化優化，設有多輪策略組合與分數評估。以下為截至 2025/6/6 之最佳效能紀錄：

- **目前最佳 overall_score**：`0.777`
- **對應 iteration**：第671次市政會議 iteration_03
- **策略組合**：A_role_definition_A1、B_structure_B1、C_summary_C1
- **使用模型**：cwchang/llama3-taide-lx-8b-chat-alpha1:latest
- **其他高分紀錄**：
  - iteration_02：overall_score 0.7069（A_role_definition_A1、B_structure_B1、E_simple_E4）
  - iteration_00：overall_score 0.6636（A_role_definition_A1、B_structure_B1、C_summary_C1）
  - iteration_14：overall_score 0.5197（A_facilitator_A2、B_structure_B1、C_context_C4）

### 效能評估指標

- length_score、structure_score、format_score、content_richness、professionalism、overall_score 等多維度評分
- 以 overall_score 作為主要優化依據

### 優化方向與建議

- 目前最佳分數已達 0.777，建議持續針對結構、內容豐富度與專業度進行微調
- 可嘗試不同策略組合與模型微調，提升穩定性與泛用性
- 詳細優化歷程與策略組合請參見 `results/iterations/` 及 docs/PROJECT_FINAL_OPTIMIZATION_REPORT.md

## 聯絡方式

- 專案維護者：[維護者姓名]
- 電子郵件：[電子郵件地址]
- GitHub Issues：[專案 Issues 頁面]
- 專案網址：[專案網址]
