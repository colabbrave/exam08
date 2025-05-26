import os
import json
from glob import glob
from pathlib import Path
import subprocess

# 設定資料夾路徑
TRANSCRIPT_DIR = "data/transcript"
STRATEGY_PATH = "config/improvement_strategies.json"
OUTPUT_DIR = "results/optimized"

# 載入所有策略
def load_strategies(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 讀取逐字稿檔案
def load_transcript(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# 呼叫 Ollama 產生優化結果
def optimize_with_model(model_name, prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"模型回應失敗：{result.stderr.strip()}")
            return ""
    except Exception as e:
        print(f"呼叫模型時發生錯誤：{e}")
        return ""

# 主流程
def main(model_name="gemma3:4b"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    strategies = load_strategies(STRATEGY_PATH)
    transcript_files = glob(os.path.join(TRANSCRIPT_DIR, "*.txt"))

    for transcript_path in transcript_files:
        transcript_name = Path(transcript_path).stem
        transcript = load_transcript(transcript_path)

        for strategy in strategies:
            # 組合提示詞
            prompt = (
                f"請根據以下策略優化會議逐字稿：\n"
                f"策略名稱：{strategy['name']}\n"
                f"策略說明：{strategy['description']}\n"
                f"範例：{strategy.get('example', '')}\n"
                f"逐字稿內容：\n{transcript}\n"
                f"請輸出優化後的會議記錄。"
            )
            result = optimize_with_model(model_name, prompt)

            # 儲存優化結果
            safe_model_name = model_name.replace(":", "_")
            output_file = os.path.join(
                OUTPUT_DIR, f"{transcript_name}__{strategy['name']}__{safe_model_name}.txt"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"已產生：{output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批次優化會議逐字稿")
    parser.add_argument("--model", type=str, default="gemma3:4b", help="Ollama 模型名稱")
    args = parser.parse_args()
    main(model_name=args.model)