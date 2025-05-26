import os
import json
from glob import glob
from pathlib import Path
import subprocess
from typing import Dict, List, Any, Optional

# 設定資料夾路徑
DATA_DIR = "data"
TRANSCRIPT_DIR = os.path.join(DATA_DIR, "transcript")
REFERENCE_DIR = os.path.join(DATA_DIR, "reference")
STRATEGY_PATH = "config/improvement_strategies.json"
OUTPUT_DIR = "results/optimized"

# 載入所有策略
def load_strategies(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 讀取逐字稿檔案
def load_transcript(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# 呼叫 Ollama 產生優化結果
def optimize_with_model(model_name: str, prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            print(f"  正在呼叫模型 {model_name} (嘗試 {attempt + 1}/{max_retries})...")
            result = subprocess.run(
                ["ollama", "run", model_name],
                input=prompt,
                capture_output=True, 
                text=True, 
                timeout=600  # 增加超時時間到10分鐘
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if not output:
                    print("  警告：模型返回了空結果")
                    continue
                return output
            else:
                print(f"  模型回應失敗 (嘗試 {attempt + 1}/{max_retries}): {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"  模型呼叫超時 (嘗試 {attempt + 1}/{max_retries})")
        except Exception as e:
            print(f"  呼叫模型時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print("  5秒後重試...")
            import time
            time.sleep(5)
    
    print(f"  錯誤：無法獲取模型 {model_name} 的有效回應")
    return ""

def find_matching_reference(transcript_name: str) -> Optional[str]:
    """尋找對應的參考會議記錄"""
    # 從逐字稿檔名推測參考檔名
    ref_prefix = transcript_name.replace("逐字稿", "會議紀錄")
    ref_pattern = os.path.join(REFERENCE_DIR, f"{ref_prefix}*.txt")
    
    matches = glob(ref_pattern)
    if matches:
        return matches[0]  # 返回第一個匹配的參考檔案
    return None

def assemble_prompt(strategy_data: Dict[str, Any], transcript: str, reference: Optional[str] = None) -> str:
    """根據策略組裝提示詞
    
    Args:
        strategy_data: 策略資料
        transcript: 會議逐字稿內容
        reference: 參考的標準會議記錄內容（可選）
    """
    components = strategy_data.get('components', {})
    
    # 基本提示
    prompt_parts = [
        "# 會議記錄優化任務\n",
        f"## 角色定義\n{components.get('role_definition', '')}\n",
        f"## 策略說明\n{strategy_data.get('description', '')}\n"
    ]
    
    # 添加指導方針
    if 'guidance' in components:
        prompt_parts.append(f"## 優化指引\n{components['guidance']}\n")
    
    # 添加參考範例（如果有）
    if reference:
        prompt_parts.extend([
            "## 參考範例\n",
            "以下是一份優質的會議記錄範例，請參考其格式和風格：\n",
            "```\n",
            reference,
            "\n```\n"
        ])
    # 否則使用策略中的範例
    elif 'example' in components and isinstance(components['example'], dict):
        ex = components['example']
        prompt_parts.append("## 範例\n")
        if 'before' in ex and 'after' in ex:
            prompt_parts.extend([
                "### 優化前\n```\n",
                ex['before'],
                "\n```\n\n### 優化後\n```\n",
                ex['after'],
                "\n```\n"
            ])
    
    # 添加避免事項
    if 'avoid' in components and components['avoid']:
        prompt_parts.append("## 避免事項\n" + "\n".join(f"- {item}" for item in components['avoid']) + "\n")
    
    # 添加格式要求
    if 'format_requirements' in components:
        fmt = components['format_requirements']
        prompt_parts.append("## 格式要求\n")
        if 'output_structure' in fmt:
            prompt_parts.append(f"### 輸出結構\n{fmt['output_structure']}\n")
        if 'length_guidance' in fmt:
            prompt_parts.append(f"### 長度指引\n{fmt['length_guidance']}\n")
    
    # 添加模板（如果存在）
    if 'template' in components:
        prompt_parts.extend([
            "## 模板\n",
            "請參考以下模板格式，但需根據實際內容調整：\n",
            "```\n",
            components['template'],
            "\n```\n"
        ])
    
    # 添加待優化的逐字稿
    prompt_parts.extend([
        "## 待優化逐字稿\n",
        "請將以下會議逐字稿進行優化：\n",
        "```\n",
        transcript,
        "\n```\n"
    ])
    
    # 最終指示
    prompt_parts.append("\n請根據以上指引，輸出優化後的會議記錄。注意保持專業、簡潔且結構清晰。")
    
    return "".join(prompt_parts)

# 主流程
def main(model_name: str = "gemma3:4b") -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    strategies_data = load_strategies(STRATEGY_PATH)
    transcript_files = glob(os.path.join(TRANSCRIPT_DIR, "*.txt"))
    
    if not transcript_files:
        print(f"警告：在 {TRANSCRIPT_DIR} 中找不到任何逐字稿檔案")
        return
    
    # 遍歷每個逐字稿檔案
    for transcript_path in transcript_files:
        transcript_name = Path(transcript_path).stem
        print(f"\n處理逐字稿: {transcript_name}")
        
        try:
            transcript = load_transcript(transcript_path)
            if not transcript.strip():
                print(f"警告：{transcript_name} 是空檔案，已跳過")
                continue
                
            # 尋找對應的參考會議記錄
            reference_path = find_matching_reference(transcript_name)
            reference = None
            if reference_path:
                try:
                    reference = load_transcript(reference_path)
                    print(f"找到參考會議記錄: {os.path.basename(reference_path)}")
                except Exception as e:
                    print(f"載入參考檔案時出錯: {e}")
            
            # 遍歷每個策略類別
            for category, strategies in strategies_data.get('strategies', {}).items():
                print(f"\n策略類別: {category}")
                
                # 遍歷類別中的每個策略
                for strategy_id, strategy in strategies.items():
                    strategy_name = strategy.get('name', '未命名策略')
                    print(f"- 套用策略: {strategy_name}")
                    
                    try:
                        # 組裝提示詞
                        prompt = assemble_prompt(strategy, transcript, reference)
                        
                        # 呼叫模型進行優化
                        result = optimize_with_model(model_name, prompt)
                        
                        if not result:
                            print(f"  警告：{strategy_name} 優化失敗")
                            continue
                        
                        # 建立輸出目錄（如果不存在）
                        category_dir = os.path.join(OUTPUT_DIR, category)
                        os.makedirs(category_dir, exist_ok=True)
                        
                        # 儲存優化結果
                        # 安全處理模型名稱，移除所有不安全字元
                        safe_model_name = "".join(c if c.isalnum() or c in ('-', '_', '.') else "_" for c in model_name)
                        # 安全處理策略名稱
                        safe_strategy_name = "".join(c if c.isalnum() or c in ('-', '_', '.') else "_" for c in strategy_name)
                        # 建立安全的輸出檔名
                        safe_filename = f"{transcript_name}__{safe_strategy_name}__{safe_model_name}.md"
                        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('_', '-', '.', ' '))
                        output_file = os.path.join(category_dir, safe_filename)
                        
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(result)
                        
                        print(f"  已產生：{os.path.relpath(output_file, OUTPUT_DIR)}")
                        
                    except Exception as e:
                        print(f"  處理策略 {strategy_name} 時發生錯誤: {e}")
                        continue
                    
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(result)
                    
                    print(f"  已產生：{output_file}")
                    
        except Exception as e:
            print(f"處理 {transcript_path} 時發生錯誤: {e}")
            continue

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批次優化會議逐字稿")
    parser.add_argument("--model", type=str, default="gemma3:4b", 
                       help="Ollama 模型名稱 (預設: gemma3:4b)")
    args = parser.parse_args()
    
    print(f"開始執行會議記錄優化 (使用模型: {args.model})")
    print("=" * 50)
    
    main(model_name=args.model)
    
    print("\n" + "=" * 50)
    print("會議記錄優化完成！")