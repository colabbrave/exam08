import os
import re
from glob import glob
from pathlib import Path
import difflib
from collections import defaultdict

REFERENCE_DIR = "data/reference"
OPTIMIZED_DIR = "results/optimized"
REPORT_DIR = "results/evaluation_reports"

def load_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

def simple_similarity(a, b):
    """使用 difflib 計算簡單相似度（可替換為更進階的評分指標）"""
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_base_name(filename):
    # 去除「逐字稿」、「會議紀錄」等後綴與副檔名
    return filename.replace("逐字稿", "").replace("會議紀錄", "").replace("__", "").replace(".txt", "").replace(".md", "")

def extract_model_name(filename):
    """從檔案名稱中提取模型名稱"""
    # 匹配最後一個雙下劃線後面的部分作為模型名稱
    match = re.search(r'__([^_].*?)(?:\.\w+)?$', filename)
    if match:
        return match.group(1).strip()
    return "unknown_model"

def extract_strategy_name(filename):
    """從檔案名稱中提取策略名稱"""
    # 匹配倒數第二個和第三個雙下劃線之間的部分作為策略名稱
    parts = [p for p in filename.split('__') if p]
    if len(parts) >= 3:
        return parts[-2]
    return "unknown_strategy"

def main():
    # 確保輸出目錄存在
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # 獲取所有優化文件（包括 .txt 和 .md 文件）
    optimized_files = []
    for ext in ('*.txt', '*.md'):
        optimized_files.extend(glob(os.path.join(OPTIMIZED_DIR, '**', ext), recursive=True))
    
    # 按模型名稱分組結果
    model_results = defaultdict(list)
    
    for opt_path in optimized_files:
        opt_name = Path(opt_path).name
        model_name = extract_model_name(opt_name)
        strategy_name = extract_strategy_name(opt_name)
        
        # 獲取會議基本名稱（去除策略和模型信息）
        base_name = opt_name.split('__')[0]
        transcript_base = get_base_name(base_name)
        
        # 在 reference 目錄下尋找對應檔案
        ref_path = None
        for ref_file in os.listdir(REFERENCE_DIR):
            if get_base_name(ref_file) == transcript_base:
                ref_path = os.path.join(REFERENCE_DIR, ref_file)
                break
                
        if not ref_path or not os.path.exists(ref_path):
            print(f"找不到對應標準答案：{transcript_base}")
            continue

        try:
            optimized_text = load_text(opt_path)
            reference_text = load_text(ref_path)
            score = simple_similarity(optimized_text, reference_text)
            
            result = {
                "transcript": transcript_base,
                "strategy": strategy_name,
                "optimized_file": opt_name,
                "reference_file": os.path.basename(ref_path),
                "similarity_score": score
            }
            model_results[model_name].append(result)
            
            print(f"{opt_name}: 相似度 {score:.4f}")
            
        except Exception as e:
            print(f"處理文件 {opt_name} 時出錯: {str(e)}")
    
    # 為每個模型生成單獨的評估報告
    for model_name, results in model_results.items():
        if not results:
            continue
            
        # 創建安全的模型名稱用於文件名
        safe_model_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in model_name)
        report_path = os.path.join(REPORT_DIR, f"evaluation_report_{safe_model_name}.csv")
        
        # 按相似度排序
        results_sorted = sorted(results, key=lambda x: x["similarity_score"], reverse=True)
        
        # 寫入CSV文件
        with open(report_path, "w", encoding="utf-8") as f:
            # 寫入表頭
            f.write("會議記錄,策略,相似度,優化檔案,參考檔案\n")
            
            # 寫入每一行數據
            for r in results_sorted:
                f.write(
                    f'"{r["transcript"]}",'  # 會議記錄名稱
                    f'"{r["strategy"]}",'       # 策略名稱
                    f'{r["similarity_score"]:.4f},'  # 相似度分數
                    f'"{r["optimized_file"]}",'  # 優化後檔案
                    f'"{r["reference_file"]}"\n'  # 參考檔案
                )
        
        print(f"\n模型 {model_name} 的評估報表已產生：{report_path}")
    
    print("\n所有評估報表已生成在 results/evaluation_reports/ 目錄下")

if __name__ == "__main__":
    main()