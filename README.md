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
   - ✅ 評估報告優化 (改為結構化數據格式)

### 當前階段

3. **提示工程優化** 🚀 進行中
   - 大模型輔助提示詞優化
   - 非監督學習優化循環
   - 自動化評估與反饋

### 後續計劃

4. **效能優化** ⏳ 未開始
   - 並行處理優化
   - 快取機制實現
   - 資源使用監控

5. **系統整合** ⏳ 未開始
   - API 服務封裝
   - 自動化部署流程
   - 監控告警系統

## 系統需求與優化

### 硬體配置

- **裝置**：MacBook Pro (M4 晶片)
- **CPU**：10 核心 (4 個效能核心 + 6 個節能核心)
- **記憶體**：16GB 統一記憶體
- **GPU**：Apple M4 整合式顯示晶片

### 模型配置

- **基礎模型**：`cwchang/llama3-taide-lx-8b-chat-alpha1:latest`
  - 使用 4-bit 量化載入
  - 主要用於會議記錄生成

- **優化模型**：`google/gemma-3-12b`
  - 使用 4-bit 量化載入
  - 用於提示詞優化和改進

## 提示工程優化架構

### 核心組件

1. **會議上下文感知模組**
   - 自動識別會議類型和特徵
   - 分析參與者角色和互動模式
   - 提取關鍵決策點和行動項目

2. **分層提示詞引擎**
   - 感知層：理解會議本質特徵
   - 策略層：選擇最優記錄策略
   - 執行層：生成結構化會議記錄

3. **動態策略管理器**
   - 多種會議類型的專用策略
   - 上下文感知的模板選擇
   - 實時策略調整機制

### 技術實現

```python
# 會議上下文分析示例
class MeetingAnalyzer:
    def analyze(self, meeting_data: dict) -> MeetingContext:
        context = MeetingContext()
        context.meeting_type = self._classify_meeting_type(meeting_data)
        context.participants = self._extract_participants(meeting_data)
        context.decision_density = self._calculate_decision_density(meeting_data)
        return context
```

### 實施路線圖

#### 階段一：基礎架構重構 (2週)
- [ ] 實現會議上下文感知模組
- [ ] 開發分層提示詞引擎基礎框架
- [ ] 創建3種基礎會議類型的適配器

#### 階段二：動態策略實現 (3週)
- [ ] 實現策略管理器
- [ ] 開發模板組件系統
- [ ] 整合上下文感知評估

#### 階段三：自適應優化 (3週)
- [ ] 實現強化學習優化器
- [ ] 設置在線學習循環
- [ ] 集成知識圖譜

### 預期效益

- **更智能的會議理解**：超越表面指標，理解會議本質
- **動態適配能力**：根據會議類型自動調整記錄策略
- **持續優化**：通過在線學習不斷改進表現
- **更好的可解釋性**：清晰的決策過程和優化路徑

### 技術棧

- **核心框架**：Python 3.9+
- **機器學習**：PyTorch, Transformers, bitsandbytes (4-bit 量化)
- **NLP工具**：sentence-transformers, NLTK
- **記憶體優化**：accelerate, vLLM (可選)
- **監控工具**：psutil, GPUtil

### 記憶體優化策略

1. **模型量化**
   - 使用 4-bit 量化技術
   - 動態量化權重矩陣
   - 啟用 Flash Attention 2 (如支援)

2. **批次處理**
   - 小批次處理輸入數據
   - 實現記憶體監控
   - 動態調整批次大小

3. **快取機制**
   - 使用 LRU 快取優化結果
   - 實現提示詞模板快取
   - 特徵向量快取

4. **資源監控**
   - 即時監控記憶體使用
   - 動態降級機制
   - 自動清理未使用的資源

### 開發原則

1. **資源效率**：優先考慮記憶體和計算效率
2. **漸進式增強**：先實現核心功能，再逐步優化
3. **可觀察性**：完善的監控和日誌記錄
4. **優雅降級**：在資源受限時自動調整功能

### 效能基準

| 任務 | 預期記憶體使用 | 預期處理時間 |
|------|--------------|------------|
| 模型載入 | ~8GB | 30-60秒 |
| 提示詞優化 | ~12GB | 5-15秒/提示 |
| 批次處理 (n=5) | ~14GB | 20-40秒 |

> **注意**：實際數值可能因系統負載和具體輸入而異

### 已知限制

1. **記憶體限制**：
   - 同時載入多個大型模型可能導致記憶體不足
   - 建議一次只載入一個模型進行推理

2. **處理時間**：
   - 複雜提示詞可能需要更長處理時間
   - 批次處理時延遲會增加

3. **建議的最佳實踐**：
   - 實現請求佇列系統
   - 設定處理超時機制
   - 定期重啟長時間運行的程序以釋放記憶體

## 最近更新

### 2025-05-28 (最新)
- 重構提示工程優化架構
- 實現分層提示詞引擎
- 新增會議上下文感知模組
- 設計動態策略管理系統
- 更新實施路線圖

### 2025-05-27
- 更新 README 文件，改進文檔結構和內容完整性
- 修復評估階段文件路徑比對問題
- 優化模型名稱處理邏輯，支援不同格式的模型名稱
- 改進評估腳本，可選擇性評估特定模型的結果
- 更新 `run_optimization.sh` 腳本，確保正確傳遞模型參數
- 改進錯誤處理和日誌記錄
- 新增模型執行時間統計功能
- 新增策略執行時間統計功能

## 最新更新 (2025-05-28)

### 新增功能與改進

1. **會議記錄質量評估增強**
   - 新增 `_evaluate_meeting_specific_quality` 方法，專門評估會議記錄的特定質量指標
   - 增加對會議信息、議程項目、決策和行動項目的專項評估
   - 優化評分權重，提高評估準確性

2. **質量改進策略 (`_strategy_improve_quality`)**
   - 新增智能質量改進策略，針對會議記錄的具體問題提供改進建議
   - 實現基於指標的自動診斷，識別會議記錄中的常見問題
   - 生成結構化的改進建議，提高優化效果

3. **優化策略選擇邏輯**
   - 改進 `_select_optimization_strategy` 方法，根據會議特定指標選擇最適合的優化策略
   - 增加策略優先級管理，確保關鍵問題優先處理
   - 添加策略效果追蹤，持續優化策略選擇

4. **提示工程改進**
   - 優化提示詞模板，提高生成結果的結構化和一致性
   - 增加上下文相關的提示，確保生成的會議記錄符合專業標準
   - 改進佔位符設計，使模板更易於使用

5. **日誌與調試增強**
   - 增加詳細的日誌記錄，便於追蹤優化過程
   - 添加錯誤處理和異常捕獲，提高系統穩定性
   - 優化日誌格式，提高可讀性

### 已知問題與後續優化

1. **質量評分偏低問題**
   - 當前質量評分普遍偏低，正在優化評分算法
   - 計劃增加更多評估維度，提高評分準確性

2. **優化效率提升**
   - 正在優化迭代策略，減少不必要的計算
   - 計劃實現增量式優化，提高響應速度

3. **模型適配性**
   - 當前主要優化針對 gemma3:12b 模型
   - 計劃擴展支持更多模型，提高通用性

### 使用建議

1. 使用最新的 `_strategy_improve_quality` 策略進行質量改進
2. 關注日誌中的改進建議，手動調整模板以獲得更好效果
3. 定期檢查優化歷史，了解策略效果
4. 根據具體需求調整質量閾值和迭代次數
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
