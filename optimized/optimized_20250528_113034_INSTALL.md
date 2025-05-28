# 會議記錄優化工具安裝與使用指南

## 會議標題：優化工具安裝與使用指南

## 與會人員：[待補充 - 需記錄參與會議的人員]

## 討論事項：
*   工具安裝與配置
*   使用方法及各選項說明
*   故障排除及常見問題

## 決議事項：
*   採納本指南，作為優化會議記錄工具的安裝和使用參考。
*   建立標準安裝流程，確保用戶能夠快速上手。

## 待辦事項：
*   完善本指南內容，包含更詳細的故障排除步驟和常見問題解答。
*   建立使用者手冊和技術文檔。
*   收集用戶反饋，持續改進工具和指南。

---

## 環境要求

本工具的安裝與運作需要滿足以下環境要求：

*   **作業系統:** Windows, macOS, Linux
*   **Python 版本:** 3.8 或更高版本
*   **CUDA 版本:** 11.7 或更高版本 (若需 GPU 加速)
*   **系統記憶體:** 至少 16GB (建議 32GB 或更多)
*   **磁碟空間:** 至少 20GB (用於模型快取)

## 安裝步驟

1.  **克隆代碼庫:**
    使用 Git 複製代碼庫到本地：
    ```bash
    git clone <repository-url>
    cd exam08_提示詞練習重啟
    ```
    (請將 `<repository-url>` 替換為實際的 Git 倉庫 URL)

2.  **創建並啟動虛擬環境 (建議):**
    *   建立虛擬環境：
        ```bash
        python -m venv venv
        ```
    *   激活虛擬環境：
        *   **Linux/macOS:** `source venv/bin/activate`
        *   **Windows:** `.\venv\Scripts\activate`

3.  **安裝依賴:**
    使用 pip 安裝所有必要的依賴包：
    ```bash
    pip install -r requirements.txt
    ```

4.  **安裝 PyTorch (若需 GPU 支援):**
    根據您的 CUDA 版本選擇合適的 PyTorch 安裝命令。 示例：
    *   **CUDA 11.8:** `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
    (請根據您的 CUDA 版本調整安裝命令)

## 下載模型

本工具支援多種語言模型。 預設使用 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest`。 首次運行時，工具會自動下載模型（約 15GB）。 請確保您有足夠的磁碟空間和穩定的網路連接。

## 使用方法

### 1. 優化單個會議記錄

```bash
python scripts/optimize_meeting_minutes.py path/to/your/meeting.txt
```
(請將 `path/to/your/meeting.txt` 替換為實際的會議記錄檔案路徑)

### 2. 批量處理多個會議記錄

```bash
# 創建輸出目錄
mkdir -p optimized_meetings

# 處理目錄中的所有 .txt 文件
for f in data/meetings/*.txt; do
    python scripts/optimize_meeting_minutes.py "$f" -o optimized_meetings
done
```

### 3. 評估優化效果

```bash
# 評估單個優化結果
python scripts/test_optimization.py --test-dir path/to/test/files --output-dir results/evaluation

# 查看評估報告
cat results/evaluation/optimization_evaluation.json
```

## 進階選項

### 使用不同的模型

```bash
python scripts/optimize_meeting_minutes.py meeting.txt --model "jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M"
```

### 調整生成長度

```bash
# 增加生成長度限制
python scripts/optimize_meeting_minutes.py meeting.txt --max-length 4096
```

## 疑難排解

### 記憶體不足

如果遇到記憶體不足錯誤，請嘗試：

1.  減少生成長度 (`--max-length`)
2.  使用較小的模型
3.  增加系統交換空間
4.  使用 CPU 模式（不推薦，速度較慢）

### 模型下載問題

如果模型下載失敗：

1.  檢查網路連接
2.  確保有足夠的磁碟空間
3.  手動下載模型並指定本地路徑

## 貢獻指南

歡迎提交問題和拉取請求！ 請確保：

1.  遵循現有的代碼風格
2.  為新功能添加測試
3.  更新相關文檔

## 授權

[在此添加授權信息]

---

## 優化結果

(本部分將根據實際優化結果進行補充，例如：優化後的會議記錄範例、優化效果的定量指標等)
