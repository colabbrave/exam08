# 會議記錄優化工具安裝與使用指南

## 會議標題：優化工具安裝與使用指南

## 與會人員：開發團隊

## 討論事項：
*   工具安裝流程
*   環境要求
*   安裝步驟
*   模型下載與使用
*   使用方法
*   疑難排解
*   貢獻指南

## 決議事項：
*   提供清晰的安裝與使用指南，方便使用者快速上手。
*   明確列出環境要求，確保使用者能夠滿足工具運行所需的條件。
*   提供詳細的步驟說明，降低使用者操作的難度。

## 待辦事項：
*   完善安裝指南，包含環境要求、安裝步驟、模型下載與使用等內容。
*   更新疑難排解部分，提供更具體的解決方案。
*   整理貢獻指南，鼓勵使用者參與開發。

---

## 環境要求

本工具的正常運行需要滿足以下環境要求：

*   **作業系統：** Windows, Linux, macOS
*   **Python 版本：** 3.8 或更高版本
*   **CUDA 版本：** 11.7 或更高版本（若需 GPU 加速）
*   **系統記憶體：** 至少 16GB (建議 32GB 或更多)
*   **磁碟空間：** 至少 20GB (用於模型快取)

## 安裝步驟

1.  **克隆代碼庫：** 使用 Git 克隆程式碼庫到本地環境。
    ```bash
    git clone <repository-url>
    cd exam08_提示詞練習重啟
    ```
2.  **創建虛擬環境 (建議)：**  建議使用虛擬環境管理 Python 依賴。
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # 或
    .\venv\Scripts\activate  # Windows
    ```
3.  **安裝依賴：**  使用 pip 安裝程式碼庫依賴。
    ```bash
    pip install -r requirements.txt
    ```
4.  **安裝 PyTorch (GPU 支援)：**  根據您的 CUDA 版本選擇合適的 PyTorch 版本。
    ```bash
    # 例如，CUDA 11.8：
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

## 模型下載

本工具支援多種語言模型。預設使用 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest`。首次運行時，工具會自動下載模型（約 15GB）。請確保您有足夠的磁碟空間和穩定的網路連接。

## 使用方法

1.  **優化單個會議記錄：**
    ```bash
    python scripts/optimize_meeting_minutes.py path/to/your/meeting.txt
    ```
2.  **批量處理多個會議記錄：**
    *   **創建輸出目錄：**
        ```bash
        mkdir -p optimized_meetings
        ```
    *   **批量處理：**
        ```bash
        for f in data/meetings/*.txt; do
            python scripts/optimize_meeting_minutes.py "$f" -o optimized_meetings
        done
        ```
3.  **評估優化效果：**
    *   **評估單個優化結果：**
        ```bash
        python scripts/test_optimization.py --test-dir path/to/test/files --output-dir results/evaluation
        ```
    *   **查看評估報告：**
        ```bash
        cat results/evaluation/optimization_evaluation.json
        ```

## 進階選項

*   **使用不同的模型：**
    ```bash
    python scripts/optimize_meeting_minutes.py meeting.txt --model "jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M"
    ```
*   **調整生成長度：**
    ```bash
    # 增加生成長度限制
    python scripts/optimize_meeting_minutes.py meeting.txt --max-length 4096
    ```

## 疑難排解

*   **記憶體不足：** 如果遇到記憶體不足錯誤，請嘗試：
    1.  減少生成長度 (`--max-length`)
    2.  使用較小的模型
    3.  增加系統交換空間
    4.  使用 CPU 模式（不推薦，速度較慢）
*   **模型下載問題：** 如果模型下載失敗：
    1.  檢查網路連接
    2.  確保有足夠的磁碟空間
    3.  手動下載模型並指定本地路徑

## 貢獻指南

歡迎提交問題和拉取請求！請確保：
*   遵循現有的代碼風格
*   為新功能添加測試
*   更新相關文檔

## 授權

[在此添加授權信息]
