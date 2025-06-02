# 會議記錄AI優化系統完整設計策略

## 系統概述

本系統設計目標：使用**小模型資源**實現**會議記錄品質的迭代優化**。核心理念是讓較大的模型（gemma3:12b）擔任「提示詞工程師」，持續優化較小模型（gemma2:9b）的會議記錄生成品質。

### 核心設計理念
- **約束優化**：在有限資源下最大化品質提升
- **漸進式改進**：每次小幅優化而非激進重構
- **結構化優化**：基於預定義策略而非自由重寫
- **可追溯性**：完整記錄優化軌跡和效果

## 系統架構設計

### 1. 環境管理設計
- **虛擬環境**：所有Python依賴隔離在專案虛擬環境中
- **Ollama服務管理**：按需啟動，統一管理，用完關閉，避免資源浪費
- **模型記憶體管理**：分階段載入模型，確保任何時刻只有一個大模型在記憶體中
- **記憶體監控**：實時監控記憶體使用，防止過載崩潰
- **模型預載機制**：啟動時檢查並預載所需模型

### 2. 資料來源
- **原始逐字稿**（transcript）：模型輸入的會議原始記錄
- **標準版會議紀錄**（reference/standard）：用於比對品質分數的黃金標準
- **預設提示詞**（如 06_call_meeting_assistant）：第一輪模型生成使用的基礎提示詞

### 3. 目錄結構規劃
```
project/
├── .venv/                          # 虛擬環境目錄
├── requirements.txt                # Python依賴清單
├── data/
│   ├── transcript.txt              # 原始逐字稿
│   └── reference.txt               # 標準版會議紀錄
├── prompts/
│   ├── base/
│   │   └── 06_call_meeting_assistant.txt  # 預設提示詞
│   ├── preloaded/                  # 預載提示詞庫
│   │   ├── professional_assistant.txt
│   │   ├── concise_summarizer.txt
│   │   └── detailed_analyzer.txt
│   ├── components/                 # 提示詞組件庫
│   │   ├── roles.json
│   │   ├── formats.json
│   │   └── instructions.json
│   └── optimized/
│       ├── v1.txt → v2.txt → v3.txt  # 版本化提示詞
│       └── optimization_log.json    # 優化記錄
├── models/
│   ├── available_models.json       # 可用模型清單
│   └── model_configs.json          # 模型配置參數
├── results/
│   └── round_{n}/
│       ├── output.txt              # 生成的會議記錄
│       ├── scores.json             # 品質分數
│       ├── memory_usage.log        # 記憶體使用記錄
│       └── comparison.txt          # 比較分析
├── config/
│   ├── improvement_strategies.json  # 30種改進策略資料庫
│   └── system_config.json          # 系統配置
├── scripts/
│   ├── setup_env.sh               # 環境初始化腳本
│   ├── optimize.py                # 主要優化程式
│   ├── run_optimization.sh        # 主執行腳本
│   ├── ollama_manager.py          # Ollama服務管理
│   ├── model_manager.py           # 模型記憶體管理
│   ├── memory_monitor.py          # 記憶體監控
│   ├── evaluate.py               # 評估模組
│   └── utils.py                  # 工具函數
└── logs/
    ├── system.log                 # 系統日誌
    ├── ollama.log                 # Ollama服務日誌
    └── memory.log                 # 記憶體監控日誌
```

## 執行流程設計

### 系統啟動流程
```bash
# 1. 虛擬環境準備
source .venv/bin/activate
pip install -r requirements.txt

# 2. 模型和提示詞預載檢查
python scripts/check_prerequisites.py --model gemma2:9b --optimizer gemma3:12b

# 3. 記憶體監控啟動
python scripts/memory_monitor.py --threshold 80 --interval 10 &

# 4. 主要優化流程
./scripts/run_optimization.sh --target-model gemma2:9b --rounds 10
```

### Ollama服務生命週期管理
```python
class OllamaManager:
    def __init__(self):
        self.service_pid = None
        self.is_running = False
    
    def start_service(self):
        if not self.is_running:
            # 啟動ollama服務
            self.service_pid = subprocess.Popen(['ollama', 'serve']).pid
            self.wait_for_service()
            self.is_running = True
    
    def stop_service(self):
        if self.is_running and self.service_pid:
            os.kill(self.service_pid, signal.SIGTERM)
            self.is_running = False
    
    def __enter__(self):
        self.start_service()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_service()
```

### 核心優化循環

#### 預備階段
1. **環境檢查**：確認虛擬環境啟動、依賴安裝完成
2. **資源檢查**：確認可用記憶體 > 4GB，磁碟空間充足  
3. **模型預載**：檢查目標模型和優化模型是否可用
4. **提示詞預載**：載入基礎提示詞和30種改進策略

#### 第一輪
1. **服務啟動**：按需啟動Ollama服務
2. **記憶體基線**：記錄開始時的記憶體使用量
3. **模型載入階段**：載入 gemma2:9b（~5.4GB記憶體）
4. **生成階段**：gemma2:9b + 預設提示詞 → 生成 output_v1
5. **模型卸載**：明確卸載 gemma2:9b，釋放記憶體
6. **評估階段**：純CPU計算，output_v1 與標準版比對 → 獲得 score_v1
7. **優化模型載入**：載入 gemma3:12b（~8.1GB記憶體）
8. **優化階段**：gemma3:12b 基於30種改進策略選擇組合 → 生成 v2.txt
9. **優化模型卸載**：卸載 gemma3:12b，釋放記憶體
10. **記錄階段**：保存所有結果、記憶體使用峰值、模型切換日誌

#### 第二輪及後續
1. **記憶體清理**：確認前一輪模型已完全卸載
2. **目標模型載入**：重新載入 gemma2:9b
3. **生成階段**：gemma2:9B + 優化後提示詞 → 生成 output_v2
4. **目標模型卸載**：卸載 gemma2:9b
5. **記憶體監控**：持續監控，確保記憶體釋放完整
6. **比較階段**：比較 score_v2 vs score_v1
   - 若提升 > 設定閾值：繼續優化流程
   - 若提升 < 閾值或下降：回退並嘗試不同策略組合
7. **條件性優化**：如需要優化，重複載入/卸載 gemma3:12b
8. **停止條件**：達到最大輪數 或 連續N輪無顯著提升 或 記憶體管理異常

**記憶體安全保證**：
- **任何時刻只有一個大模型在記憶體中**
- **模型切換時強制等待2秒確保完全釋放**  
- **記憶體使用峰值不超過單一最大模型(8.1GB) + 系統開銷(2GB) = 10.1GB**

#### 結束階段
1. **Ollama關閉**：優雅關閉Ollama服務
2. **記憶體報告**：生成記憶體使用統計報告
3. **結果整理**：整理所有輸出檔案和日誌
4. **環境清理**：清理暫存檔案

### 安全機制
```python
# 核心邏輯包含模型記憶體管理
def optimize_prompt(current_prompt, score_history, model_manager, max_retries=3):
    # 提升幅度檢查
    if len(score_history) >= 2:
        recent_improvement = score_history[-1] - score_history[-2]
        if recent_improvement < 0.01:  # 提升過小
            return "early_stop", current_prompt
    
    # 確保優化模型載入，目標模型卸載
    model_manager.switch_to_optimizer()
    
    # 結構化策略選擇，而非自由重寫
    selected_strategies = gemma3_select_strategies(...)
    new_prompt = assemble_prompt(current_prompt, selected_strategies)
    
    # 卸載優化模型，為下一輪做準備
    model_manager.unload_current()
    
    return "continue", new_prompt

# 模型記憶體管理器
class ModelManager:
    def __init__(self, target_model="gemma2:9b", optimizer_model="gemma3:12b"):
        self.target_model = target_model
        self.optimizer_model = optimizer_model
        self.current_model = None
        self.logger = self.setup_logger()
    
    def setup_logger(self):
        logger = logging.getLogger('model_manager')
        handler = logging.FileHandler('logs/model_management.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def switch_to_target(self):
        """切換到目標模型（用於生成會議記錄）"""
        self._switch_model(self.target_model)
    
    def switch_to_optimizer(self):
        """切換到優化模型（用於優化提示詞）"""
        self._switch_model(self.optimizer_model)
    
    def _switch_model(self, model_name):
        if self.current_model == model_name:
            self.logger.info(f"模型 {model_name} 已載入，無需切換")
            return
            
        # 卸載當前模型
        if self.current_model:
            self.unload_model(self.current_model)
        
        # 載入新模型
        self.load_model(model_name)
        self.current_model = model_name
    
    def load_model(self, model_name):
        """載入指定模型"""
        self.logger.info(f"載入模型: {model_name}")
        start_time = time.time()
        
        # 預載模型到記憶體
        subprocess.run([
            'ollama', 'run', model_name, 
            'echo "模型預載完成"'
        ], capture_output=True)
        
        load_time = time.time() - start_time
        self.logger.info(f"模型 {model_name} 載入完成，耗時: {load_time:.2f}秒")
    
    def unload_model(self, model_name):
        """卸載指定模型"""
        self.logger.info(f"卸載模型: {model_name}")
        
        try:
            # 明確卸載模型
            subprocess.run(['ollama', 'ps'], capture_output=True)
            subprocess.run(['ollama', 'stop', model_name], capture_output=True)
            
            # 等待記憶體釋放
            time.sleep(2)
            
            self.logger.info(f"模型 {model_name} 已卸載")
            
        except Exception as e:
            self.logger.error(f"卸載模型 {model_name} 時發生錯誤: {e}")
    
    def unload_current(self):
        """卸載當前模型"""
        if self.current_model:
            self.unload_model(self.current_model)
            self.current_model = None
    
    def get_model_status(self):
        """獲取模型狀態"""
        try:
            result = subprocess.run(['ollama', 'ps'], 
                                  capture_output=True, text=True)
            return {
                'current_model': self.current_model,
                'running_models': result.stdout,
                'memory_safe': self.current_model is not None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload_current()
```

## 30種改進策略資料庫

### 分類架構
改進策略按六大維度分類，每維度5個具體策略：

#### 1. 角色定義強化
提升AI的專業身份認知和權威性

**A1. 專業秘書角色**
- **描述**：強化專業會議記錄人員身份
- **組件**：你是資深會議記錄專員，具備15年政府機關會議記錄經驗，熟悉各類會議流程和決策記錄要求。
- **預期效果**：提升專業度和權威性

**A2. 分析師角色**
- **描述**：增加分析思維能力
- **組件**：你是會議分析師，擅長從討論中提取核心議題、識別不同立場、歸納決策邏輯。
- **預期效果**：強化邏輯分析能力

**A3. 台灣政府專家**
- **描述**：專精台灣政府會議文化
- **組件**：你是台灣政府會議專家，深度理解台灣公部門的議事規則、決策流程和文書格式。
- **預期效果**：提升本土化適應性

**A4. 效率專家**
- **描述**：注重效率和行動導向
- **組件**：你是會議效率專家，專注於提取可執行的決議和明確的後續行動。
- **預期效果**：提升行動導向性

**A5. 品質控制者**
- **描述**：嚴格的品質標準
- **組件**：你是會議記錄品質控制專員，確保每份記錄都準確、完整、可追溯。
- **預期效果**：提升記錄品質

#### 2. 結構格式優化
建立清晰的資訊組織架構

**B1. 階層式結構**
- **描述**：建立清晰的資訊階層
- **組件**：請按照以下階層結構整理：\n## 會議概要\n### 基本資訊\n### 與會人員\n## 討論議題\n### 議題一：[標題]\n#### 討論要點\n#### 不同觀點\n#### 決議結果\n## 行動計畫\n### 責任歸屬\n### 時程安排
- **預期效果**：提升結構清晰度

**B2. 時間軸結構**
- **描述**：按時間順序組織內容
- **組件**：請按會議進行的時間順序記錄：【開場】→【報告階段】→【討論階段】→【決議階段】→【結論】，每個階段標註時間要點。
- **預期效果**：強化時間邏輯

**B3. 決策導向結構**
- **描述**：突出決策過程和結果
- **組件**：重點結構：🎯議題背景 → 💭討論觀點 → ⚖️評估考量 → ✅最終決策 → 📋後續行動
- **預期效果**：強化決策記錄

**B4. 利害關係人結構**
- **描述**：按發言者角色組織
- **組件**：按角色整理發言：【主席觀點】【市長指示】【局處報告】【議員質詢】【民眾意見】【專家建議】
- **預期效果**：清晰角色立場

**B5. 摘要優先結構**
- **描述**：重要資訊前置
- **組件**：開頭必須包含：📊會議成果摘要 | 🔑關鍵決議 | ⏰重要時程 | 👥責任分工
- **預期效果**：提升瀏覽效率

#### 3. 內容深度增強
提升記錄的分析深度和洞察力

**C1. 邏輯挖掘**
- **描述**：深入分析因果邏輯
- **組件**：請深入挖掘：每個決議的【起因】→【考量因素】→【預期效果】→【風險評估】，不只記錄結果，更要呈現思考過程。
- **預期效果**：提升邏輯深度

**C2. 衝突觀點分析**
- **描述**：識別和分析不同觀點
- **組件**：當出現不同意見時，請明確記錄：【甲方觀點及理由】vs【乙方觀點及理由】→【爭議焦點】→【協調結果】
- **預期效果**：呈現討論完整性

**C3. 影響評估**
- **描述**：分析決策影響範圍
- **組件**：對重要決議進行影響分析：🏛️對機關影響 | 👥對民眾影響 | 💰預算影響 | ⏱️時程影響 | 🌐政策影響
- **預期效果**：提升決策深度

**C4. 背景脈絡補充**
- **描述**：增加必要背景資訊
- **組件**：補充重要背景：此議題的【歷史脈絡】【相關政策】【先前決議】【外部環境】，讓記錄更具完整性。
- **預期效果**：增強理解性

**C5. 行動細節化**
- **描述**：具體化行動計畫
- **組件**：行動項目必須包含：【具體任務】【負責單位/人員】【完成時限】【預期成果】【檢核方式】【報告時程】
- **預期效果**：提升執行性

#### 4. 格式約束精確化
統一和規範輸出格式

**D1. 強化Markdown格式**
- **描述**：統一且豐富的格式標記
- **組件**：嚴格使用格式：**重要決議**用粗體、`專有名詞`用代碼格式、> 重要引言用引用、- [ ] 待辦事項用核取方塊
- **預期效果**：提升格式統一性

**D2. 表情符號分類**
- **描述**：用符號快速識別內容類型
- **組件**：內容分類標記：📋議題 📊數據 💡建議 ⚠️注意 ✅通過 ❌否決 🔄延期 📅排程 💰預算 👥人事
- **預期效果**：提升視覺識別度

**D3. 表格化結構資訊**
- **描述**：重要資訊以表格呈現
- **組件**：決議事項用表格：| 項目 | 內容 | 負責人 | 期限 | 狀態 |\n預算項目用表格：| 科目 | 金額 | 用途 | 來源 |
- **預期效果**：提升資訊結構化

**D4. 編號系統**
- **描述**：建立完整編號體系
- **組件**：建立編號系統：議題編號(A1、A2...)、決議編號(D1、D2...)、行動編號(T1、T2...)，便於追蹤和引用。
- **預期效果**：提升追蹤性

**D5. 長度控制**
- **描述**：控制各部分篇幅比例
- **組件**：篇幅控制：會議概要(10%)、討論過程(40%)、決議事項(30%)、後續行動(20%)，確保重點突出。
- **預期效果**：提升重點聚焦

#### 5. 語言風格調整
優化語言表達方式

**E1. 正式公文風格**
- **描述**：採用政府公文語調
- **組件**：使用正式用語：「經討論決議」「請相關單位辦理」「依據會議決議」「俟完成後報核」等政府慣用語。
- **預期效果**：提升正式性

**E2. 白話文風格**
- **描述**：使用清晰易懂的語言
- **組件**：使用平實語言，避免過度修飾。重點在於清楚傳達，不在於文字華麗。複雜概念要用簡單詞彙解釋。
- **預期效果**：提升可讀性

**E3. 主動語態**
- **描述**：多用主動語態增強行動感
- **組件**：優先使用主動語態：「市長指示」而非「經市長指示」、「議員建議」而非「經議員建議」。
- **預期效果**：增強行動力

**E4. 簡潔精準**
- **描述**：去除冗詞贅字
- **組件**：每句話都要有實質內容，避免「關於...方面」「有關...部分」等空泛用詞。用詞精準，一詞表一意。
- **預期效果**：提升簡潔性

**E5. 台灣在地化用語**
- **描述**：使用台灣慣用表達
- **組件**：使用台灣在地用語：「議會」「市政府」「局處」「議員」「里長」「區公所」等，避免大陸用語。
- **預期效果**：提升本土化

#### 6. 品質控制機制
確保輸出品質的穩定性

**F1. 完整性檢核**
- **描述**：確保資訊完整不遺漏
- **組件**：檢核清單：□會議基本資訊 □所有議題都有記錄 □每個決議都有負責人 □時程都有明確期限 □重要數據都有記錄
- **預期效果**：提升完整性

**F2. 準確性驗證**
- **描述**：核對重要資訊準確性
- **組件**：重要資訊雙重確認：人名、職稱、金額、日期、法條、政策名稱等關鍵資訊需要特別仔細核對。
- **預期效果**：提升準確性

**F3. 一致性維護**
- **描述**：保持用詞和格式一致
- **組件**：維護一致性：同一人物用同一稱謂、同一概念用同一用詞、同類資訊用同一格式。
- **預期效果**：提升一致性

**F4. 可執行性焦點**
- **描述**：確保行動項目可執行
- **組件**：每個行動項目都要通過「5W1H檢驗」：Who(誰)、What(什麼)、When(何時)、Where(何地)、Why(為何)、How(如何)。
- **預期效果**：提升執行性

**F5. 可追溯性增強**
- **描述**：建立清晰的追蹤機制
- **組件**：建立追蹤機制：每個決議標註「前次會議相關決議」「本次變更內容」「下次檢討時程」。
- **預期效果**：提升追蹤性

## 策略使用指南

### 選擇原則
1. **每次優化選擇2-3個不同類別的策略組合使用**
2. **優先類別**：結構格式優化 > 內容深度增強 > 品質控制機制
3. **避免衝突組合**：
   - 正式公文風格 vs 白話文風格（語言風格衝突）
   - 長度控制 vs 背景脈絡補充（篇幅要求衝突）

### 推薦組合方案

#### 初次優化組合
- A1 專業秘書角色
- B1 階層式結構  
- F1 完整性檢核

#### 決策導向強化組合
- B3 決策導向結構
- C1 邏輯挖掘
- F4 可執行性焦點

#### 格式標準化組合
- D1 強化Markdown格式
- D4 編號系統
- F3 一致性維護

## 參數化設計

### Shell Script主執行介面
```bash
#!/bin/bash
# run_optimization.sh - 主要執行腳本

# 預設參數
DEFAULT_TARGET_MODEL="gemma2:9b"
DEFAULT_OPTIMIZER_MODEL="gemma3:12b" 
DEFAULT_BASE_PROMPT="prompts/base/06_call_meeting_assistant.txt"
DEFAULT_ROUNDS=10
DEFAULT_MEMORY_THRESHOLD=80

# 參數解析
while [[ $# -gt 0 ]]; do
  case $1 in
    --target-model)
      TARGET_MODEL="$2"
      shift 2
      ;;
    --optimizer-model)
      OPTIMIZER_MODEL="$2"
      shift 2
      ;;
    --base-prompt)
      BASE_PROMPT="$2"
      shift 2
      ;;
    --rounds)
      ROUNDS="$2"
      shift 2
      ;;
    --memory-threshold)
      MEMORY_THRESHOLD="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --target-model MODEL       目標優化模型 (預設: gemma2:9b)"
      echo "  --optimizer-model MODEL    提示詞優化模型 (預設: gemma3:12b)"
      echo "  --base-prompt FILE         基礎提示詞檔案"
      echo "  --rounds N                 最大優化輪數 (預設: 10)"
      echo "  --memory-threshold N       記憶體警告閾值% (預設: 80)"
      exit 0
      ;;
    *)
      echo "未知參數: $1"
      exit 1
      ;;
  esac
done

# 設定預設值
TARGET_MODEL=${TARGET_MODEL:-$DEFAULT_TARGET_MODEL}
OPTIMIZER_MODEL=${OPTIMIZER_MODEL:-$DEFAULT_OPTIMIZER_MODEL}
BASE_PROMPT=${BASE_PROMPT:-$DEFAULT_BASE_PROMPT}
ROUNDS=${ROUNDS:-$DEFAULT_ROUNDS}
MEMORY_THRESHOLD=${MEMORY_THRESHOLD:-$DEFAULT_MEMORY_THRESHOLD}

# 執行流程
echo "啟動優化流程..."
echo "目標模型: $TARGET_MODEL"
echo "優化模型: $OPTIMIZER_MODEL"
echo "基礎提示詞: $BASE_PROMPT"
echo "優化輪數: $ROUNDS"

# 1. 環境檢查和啟動
source .venv/bin/activate
python scripts/check_prerequisites.py \
  --target-model "$TARGET_MODEL" \
  --optimizer-model "$OPTIMIZER_MODEL" \
  --base-prompt "$BASE_PROMPT"

# 2. 記憶體監控啟動
python scripts/memory_monitor.py \
  --threshold "$MEMORY_THRESHOLD" \
  --interval 10 \
  --log-file "logs/memory.log" &
MEMORY_MONITOR_PID=$!

# 3. 主要優化程式
python scripts/optimize.py \
  --target-model "$TARGET_MODEL" \
  --optimizer-model "$OPTIMIZER_MODEL" \
  --base-prompt "$BASE_PROMPT" \
  --rounds "$ROUNDS" \
  --memory-threshold "$MEMORY_THRESHOLD"

# 4. 清理
kill $MEMORY_MONITOR_PID 2>/dev/null
echo "優化流程完成"
```

### Python程式參數設計
```bash
python scripts/optimize.py \
  --target-model gemma2:9b \           # 目標優化模型
  --optimizer-model gemma3:12b \       # 提示詞優化模型
  --base-prompt prompts/base/06_call_meeting_assistant.txt \  # 基礎提示詞
  --rounds 10 \                        # 最大優化輪數
  --min-improvement 0.01 \             # 最小改善閾值
  --max-retries 3 \                    # 最大重試次數
  --save-all-versions true \           # 保存所有版本
  --evaluation-metrics rouge,bertscore \ # 評估指標
  --memory-threshold 80 \              # 記憶體警告閾值
  --memory-limit 90 \                  # 記憶體強制停止閾值
  --cleanup-interval 5                 # 記憶體清理間隔(輪數)
```

### 模型預載檢查機制
```python
# scripts/check_prerequisites.py
def check_model_availability(model_name):
    """檢查模型是否可用"""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        available_models = result.stdout
        return model_name in available_models
    except Exception as e:
        return False

def preload_models(target_model, optimizer_model):
    """預載必要模型"""
    models_to_check = [target_model, optimizer_model]
    
    for model in models_to_check:
        if not check_model_availability(model):
            print(f"正在下載模型: {model}")
            subprocess.run(['ollama', 'pull', model])
        else:
            print(f"模型已存在: {model}")

def load_available_prompts():
    """載入可用的提示詞範本"""
    prompt_dir = Path("prompts/preloaded")
    available_prompts = {}
    
    for prompt_file in prompt_dir.glob("*.txt"):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            available_prompts[prompt_file.stem] = f.read()
    
    return available_prompts
```

### 配置檔案設計
```json
{
  "system_config": {
    "virtual_env_path": ".venv",
    "default_models": {
      "target": "gemma2:9b",
      "optimizer": "gemma3:12b",
      "fallback_target": "phi3:latest",
      "fallback_optimizer": "gemma3:12b"
    },
    "memory_management": {
      "warning_threshold": 80,
      "critical_threshold": 90,
      "cleanup_interval": 5,
      "monitoring_interval": 10
    },
    "ollama_config": {
      "startup_timeout": 30,
      "shutdown_timeout": 10,
      "health_check_interval": 5
    }
  },
  "optimization_config": {
    "max_strategies_per_round": 3,
    "strategy_selection_mode": "smart",
    "early_stop_threshold": 0.005,
    "score_improvement_window": 3,
    "max_consecutive_failures": 3
  },
  "evaluation_config": {
    "primary_metric": "bertscore",
    "secondary_metrics": ["rouge-1", "rouge-l"],
    "weight_distribution": {"bertscore": 0.6, "rouge-1": 0.2, "rouge-l": 0.2}
  },
  "logging_config": {
    "log_level": "INFO",
    "log_rotation": "daily",
    "max_log_files": 7
  }
}
```

## 監控和日誌

### 記憶體監控機制
```python
# scripts/memory_monitor.py
import psutil
import time
import logging
from pathlib import Path

class MemoryMonitor:
    def __init__(self, threshold=80, critical_threshold=90, interval=10):
        self.threshold = threshold          # 警告閾值
        self.critical_threshold = critical_threshold  # 危險閾值
        self.interval = interval           # 檢查間隔(秒)
        self.logger = self.setup_logger()
        
    def setup_logger(self):
        logger = logging.getLogger('memory_monitor')
        handler = logging.FileHandler('logs/memory.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used
        }
    
    def monitor(self):
        while True:
            memory_info = self.get_memory_usage()
            percent = memory_info['percent']
            
            if percent >= self.critical_threshold:
                self.logger.critical(
                    f"記憶體使用率危險: {percent:.1f}% - 建議立即停止程序"
                )
                # 可以觸發緊急停止機制
                self.trigger_emergency_stop()
                
            elif percent >= self.threshold:
                self.logger.warning(
                    f"記憶體使用率過高: {percent:.1f}% - 建議清理"
                )
                # 可以觸發清理機制
                self.trigger_cleanup()
                
            else:
                self.logger.info(
                    f"記憶體使用正常: {percent:.1f}%"
                )
            
            time.sleep(self.interval)
    
    def trigger_cleanup(self):
        """觸發記憶體清理"""
        import gc
        gc.collect()
        self.logger.info("執行垃圾回收清理")
    
    def trigger_emergency_stop(self):
        """觸發緊急停止"""
        Path("EMERGENCY_STOP").touch()
        self.logger.critical("創建緊急停止檔案")
```

### Ollama服務監控
```python
# scripts/ollama_manager.py
import subprocess
import time
import signal
import os
import requests
from pathlib import Path

class OllamaManager:
    def __init__(self, startup_timeout=30, health_check_interval=5):
        self.service_pid = None
        self.is_running = False
        self.startup_timeout = startup_timeout
        self.health_check_interval = health_check_interval
        self.log_file = Path("logs/ollama.log")
        
    def start_service(self):
        if self.is_running:
            return True
            
        print("啟動 Ollama 服務...")
        
        # 確保日誌目錄存在
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 啟動服務並重定向輸出
        with open(self.log_file, 'a') as log_f:
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=log_f,
                stderr=subprocess.STDOUT
            )
            self.service_pid = process.pid
        
        # 等待服務啟動
        if self.wait_for_service():
            self.is_running = True
            print(f"Ollama 服務已啟動 (PID: {self.service_pid})")
            return True
        else:
            print("Ollama 服務啟動失敗")
            return False
    
    def wait_for_service(self):
        """等待服務啟動並可用"""
        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        return False
    
    def stop_service(self):
        if self.is_running and self.service_pid:
            print("關閉 Ollama 服務...")
            try:
                os.kill(self.service_pid, signal.SIGTERM)
                # 等待優雅關閉
                time.sleep(2)
                # 如果還在運行，強制關閉
                try:
                    os.kill(self.service_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # 程序已經結束
            except ProcessLookupError:
                pass  # 程序已經結束
            
            self.is_running = False
            self.service_pid = None
            print("Ollama 服務已關閉")
    
    def health_check(self):
        """健康檢查"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def __enter__(self):
        self.start_service()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_service()
```

### 每輪記錄內容
- **策略使用記錄**：使用的策略組合及其編號
- **分數變化趨勢**：總分和各子指標的詳細記錄
- **提示詞差異**：策略應用前後的提示詞變化
- **性能指標**：生成時間、評估時間、記憶體使用峰值
- **模型管理記錄**：模型載入/卸載時間、記憶體釋放狀況、切換成功率
- **系統狀態**：Ollama服務狀態、記憶體使用率、磁碟使用量
- **錯誤記錄**：回退次數、錯誤原因、恢復措施

### 日誌結構設計
```
logs/
├── system.log              # 主要系統日誌
├── ollama.log              # Ollama服務日誌  
├── memory.log              # 記憶體監控日誌
├── model_management.log    # 模型載入/卸載日誌
├── optimization.log        # 優化過程日誌
└── error.log               # 錯誤日誌
```

### 即時監控界面（可選）
```python
# 包含模型狀態的監控界面
def display_status(model_manager):
    while True:
        memory_info = get_memory_usage()
        ollama_status = check_ollama_health()
        model_status = model_manager.get_model_status()
        current_round = get_current_round()
        
        os.system('clear')  # Linux/Mac
        print("=== 會議記錄優化系統監控 ===")
        print(f"記憶體使用: {memory_info['percent']:.1f}%")
        print(f"Ollama狀態: {'🟢 運行中' if ollama_status else '🔴 離線'}")
        print(f"當前模型: {model_status.get('current_model', '無')}")
        print(f"當前輪次: {current_round}")
        print(f"記憶體安全: {'✅ 安全' if model_status.get('memory_safe', False) else '⚠️ 風險'}")
        print(f"最後更新: {time.strftime('%H:%M:%S')}")
        
        time.sleep(5)
```

### 成功指標監控
- **分數提升率**：相較於基礎版本的改善幅度 (目標: >10%)
- **穩定性**：連續輪次的分數波動程度 (目標: <5%)
- **效率**：達到目標分數所需的輪數 (目標: <10輪)
- **資源使用**：記憶體使用峰值 (目標: <10.1GB)
- **模型切換效率**：平均載入/卸載時間 (目標: <30秒)
- **可重現性**：相同策略組合的結果一致性 (目標: >85%)
- **錯誤率**：優化過程中的失敗比例 (目標: <20%)

## 實現建議

### 環境設置優先級
1. **第一階段**：虛擬環境和基礎設施
   - 虛擬環境建立和依賴管理
   - Ollama服務管理機制  
   - 記憶體監控基礎設施
   - 基礎日誌系統

2. **第二階段**：核心功能模組
   - 30策略資料庫和基礎框架
   - 模型預載和檢查機制
   - 提示詞版本管理系統
   - 基礎評估模組

3. **第三階段**：智慧優化邏輯
   - 智慧策略選擇和組合邏輯
   - 多維度評估和品質控制
   - 自動回退和錯誤恢復
   - 記憶體自動清理機制

4. **第四階段**：使用者介面和分析
   - Shell script使用者介面
   - 即時監控界面（可選）
   - 結果分析和可視化工具
   - 完整的文檔和使用指南

### 關鍵技術實現點

#### 虛擬環境管理
```bash
# setup_env.sh - 環境初始化腳本
#!/bin/bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "虛擬環境已建立"
fi

source .venv/bin/activate
pip install --upgrade pip

# 安裝依賴
pip install -r requirements.txt

echo "環境設置完成"
echo "請執行: source .venv/bin/activate"
```

#### 模型記憶體管理策略
```python
# 主要優化流程中的模型管理
def run_optimization_round(model_manager, prompt, transcript, reference):
    """單輪優化流程，確保記憶體安全"""
    
    # 階段1：生成會議記錄
    model_manager.switch_to_target()
    output = generate_meeting_minutes(prompt, transcript)
    model_manager.unload_current()  # 立即釋放記憶體
    
    # 階段2：評估（純CPU，無需大模型）
    score = evaluate_output(output, reference)
    
    # 階段3：優化提示詞  
    model_manager.switch_to_optimizer()
    optimized_prompt = optimize_prompt_with_strategies(prompt, output, score)
    model_manager.unload_current()  # 立即釋放記憶體
    
    return output, score, optimized_prompt

# 記憶體安全保證
def ensure_memory_safety():
    """確保記憶體使用安全"""
    memory_usage = psutil.virtual_memory().percent
    
    if memory_usage > 85:
        # 強制清理
        subprocess.run(['ollama', 'ps'])  # 檢查運行中的模型
        subprocess.run(['ollama', 'stop', '--all'])  # 停止所有模型
        gc.collect()  # Python垃圾回收
        time.sleep(3)  # 等待記憶體釋放
        
        return memory_usage < 80  # 確認清理成功
    
    return True
```

#### 資源管理策略
- **記憶體限制**：任何時刻只載入一個大模型，峰值不超過10.1GB
- **服務生命週期**：Ollama服務按需啟動，完成後立即關閉
- **模型切換機制**：明確的載入/卸載序列，強制等待記憶體釋放
- **暫存清理**：定期清理暫存檔案和模型快取
- **錯誤恢復**：自動檢測記憶體異常並回退到穩定狀態

#### 模型預載機制
```python
def ensure_models_available(target_model, optimizer_model):
    """確保所需模型可用，並測試記憶體需求"""
    required_models = [target_model, optimizer_model]
    
    for model in required_models:
        if not check_model_exists(model):
            print(f"模型 {model} 不存在，開始下載...")
            download_model(model)
        else:
            print(f"模型 {model} 已就緒")
    
    # 測試記憶體需求
    test_memory_requirements(target_model, optimizer_model)
    
    return True

def test_memory_requirements(target_model, optimizer_model):
    """測試模型記憶體需求"""
    print("測試模型記憶體需求...")
    
    # 測試較大的模型（通常是優化模型）
    larger_model = optimizer_model if "12b" in optimizer_model else target_model
    
    with ModelManager() as manager:
        manager._switch_model(larger_model)
        memory_peak = psutil.virtual_memory().percent
        print(f"模型 {larger_model} 記憶體使用峰值: {memory_peak:.1f}%")
        
        if memory_peak > 90:
            raise MemoryError(f"記憶體不足以運行 {larger_model}")
    
    print("記憶體需求測試通過")
```

### 開發優先順序調整
考慮到記憶體管理的關鍵性，建議調整開發順序：

1. **基礎設施優先**：虛擬環境管理、Ollama服務控制、基礎日誌系統
2. **記憶體管理次要**：ModelManager類、記憶體監控、自動清理機制
3. **安全機制第三**：錯誤恢復、緊急停止、健康檢查機制
4. **核心功能第四**：策略選擇和優化邏輯、評估模組
5. **使用者體驗最後**：Shell介面優化、可視化監控、分析工具

---

## 總結

本設計策略的核心價值在於**在資源約束下實現智慧優化**。通過30種結構化改進策略的組合應用，系統能夠在不依賴大型模型或雲端資源的情況下，持續提升會議記錄的生成品質。

### 關鍵創新點
- **約束優化**取代自由重寫，確保可控性
- **結構化策略**取代隨機嘗試，提升效率
- **漸進式改進**取代激進變革，降低風險
- **多維度評估**取代單一指標，提升品質

### 技術規範核心特色
- **虛擬環境隔離**：確保依賴管理和環境一致性
- **資源精確管理**：Ollama按需啟動，用完即關，避免資源浪費
- **模型記憶體分離**：分階段載入模型，任何時刻只有一個大模型在記憶體中，峰值不超過10.1GB
- **預載檢查機制**：啟動前確認所有必要資源，避免運行時錯誤
- **即時記憶體監控**：防止系統過載崩潰，確保穩定運行

### 工程化設計亮點
- **Shell介面整合**：統一的參數化執行入口
- **多層次日誌系統**：系統、服務、記憶體、模型管理、優化的完整記錄
- **智慧模型切換**：自動載入/卸載機制，確保記憶體使用最優化
- **自動錯誤恢復**：記憶體不足時的自動清理和回退機制  
- **健康檢查機制**：服務狀態和模型狀態的持續監控和自動修復

這個設計既保持了自動化優化的智慧性，又在小模型環境下確保了穩定性和可預測性。特別是加入的四項技術規範（虛擬環境、Ollama管理、模型預載、記憶體監控），讓系統在資源有限的環境下仍能穩定可靠地運行。

**核心理念**：工程可靠性優於算法優雅性。在小模型環境下，穩定的基礎設施比複雜的優化算法更重要。這個設計確保了系統在追求品質提升的同時，不會因為資源管理不當而崩潰或不穩定。

**記憶體管理的戰略意義**：通過精確的模型載入/卸載控制，系統能夠在有限的硬體資源上運行大型模型組合。gemma3:12b(8.1GB) + gemma2:9b(5.4GB) 的總需求為13.5GB，但通過分階段管理，實際峰值記憶體需求只有10.1GB，讓更多用戶能夠在普通硬體上享受大模型的優化能力。

**工程哲學的體現**：這個設計將「約束」轉化為「優勢」。記憶體限制迫使我們設計出更精巧的模型切換機制，結果反而比同時載入所有模型更加穩定可靠。這正是小模型時代工程實踐的精髓：用系統設計的智慧彌補硬體資源的限制。