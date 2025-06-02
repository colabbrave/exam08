以下是本專案「會議記錄優化與評估系統」的全程資訊作業流程，涵蓋從環境建置、資料準備、優化疊代、評分、策略管理到結果產出與擴充：

---

## 1. 環境建置

- 安裝 Python 3.8+，建議使用虛擬環境
- 安裝 Ollama 服務（本地 LLM 推理）
- 下載專案原始碼並安裝依賴
  ```bash
  git clone https://github.com/colabbrave/exam08.git
  cd exam08
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  # .\venv\Scripts\activate  # Windows
  pip install -r requirements.txt
  ollama pull cwchang/llama3-taide-lx-8b-chat-alpha1:latest
  ```

---

## 2. 資料準備

- 將原始逐字稿放入 `data/transcript/`
- 將標準 reference 會議記錄放入 `data/reference/`
- 可自訂/擴充提示詞於 `prompts/`，策略於 `config/improvement_strategies.json`

---

## 3. 優化與評估主流程

### (1) 啟動優化腳本
- 執行 `./run_optimization.sh`，可指定模型與疊代輪數

### (2) 自動 reference 配對
- 系統自動比對逐字稿與 reference，找不到則用逐字稿自身作為 reference

### (3) minutes 生成
- 由本地 LLM（cwchang/llama3-taide-lx-8b-chat-alpha1:latest）根據逐字稿、模板、策略、提示詞自動產生 minutes

### (4) 多指標自動評分
- 產生的 minutes 會自動與 reference 進行多指標評分（BERTScore、TaiwanScore、ROUGE、結構化等）

### (5) 策略與提示詞自動優化
- 每輪疊代後，LLM（如 gemma3:12b）根據 minutes/reference/分數自動建議新策略與提示詞，進行閉環優化

### (6) 疊代與 early stopping
- 根據分數提升與策略效果，動態調整策略組合，達到品質閾值或最大輪數自動停止

### (7) 結果儲存
- 儲存最佳 minutes（.json/.txt）、評分報告、優化歷史與日誌於 `results/`、`logs/`

---

## 4. 評分模組

- 內建多指標評分（BERTScore F1、TaiwanScore、ROUGE-1/2/L、結構化程度、行動項目明確性、格式一致性）
- 支援批次評分與多指標加權，並可擴充自訂指標與權重
- 每輪 minutes 產生後自動評分，作為疊代優化依據

---

## 5. 優化策略管理

- 內建 30 種優化策略，分為六大維度（角色、結構、內容、格式、語言、品質）
- 策略可於 `config/improvement_strategies.json` 擴充
- 每輪疊代可組合2-3個不同維度策略，避免衝突
- LLM 自動建議新策略組合，並自動組合最佳策略與提示詞

---

## 6. 提示工程與上下文感知

- 會議上下文感知模組自動識別會議類型、參與者、決策密度
- 分層提示詞引擎根據上下文與策略自動生成最佳 prompt
- 動態策略管理器根據分數與歷史自動調整策略組合

---

## 7. 結果產出與擴充

- 優化 minutes、評分報告、策略組合、日誌等自動儲存於對應目錄
- 支援多模型切換、記憶體安全管理、批次自動化運行
- 可擴充自訂策略、提示詞、評分指標與自動化腳本

---

## 8. 進階參考

- 詳細策略設計與推薦組合請見 `docu/complete_design_strategy-2.md`
- 策略與評分細節可於 `config/improvement_strategies.json`、`scripts/evaluate.py` 查閱
- 歡迎貢獻新策略、指標與自動化流程

---

如需更細緻的流程範例、策略組合建議或自動化腳本說明，請參考專案內文檔或提出需求！
