import os
from glob import glob
from pathlib import Path
import difflib

REFERENCE_DIR = "data/reference"
OPTIMIZED_DIR = "results/optimized"
REPORT_PATH = "results/evaluation_report.csv"

def load_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

def simple_similarity(a, b):
    """使用 difflib 計算簡單相似度（可替換為更進階的評分指標）"""
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_base_name(filename):
    # 去除「逐字稿」、「會議紀錄」等後綴與副檔名
    return filename.replace("逐字稿", "").replace("會議紀錄", "").replace("__", "").replace(".txt", "")

def main():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    optimized_files = glob(os.path.join(OPTIMIZED_DIR, "*.txt"))
    results = []

    for opt_path in optimized_files:
        opt_name = Path(opt_path).stem
        transcript_base = get_base_name(opt_name.split("__")[0])
        # 在 reference 目錄下尋找對應檔案
        ref_path = None
        for ref_file in os.listdir(REFERENCE_DIR):
            if get_base_name(ref_file) == transcript_base:
                ref_path = os.path.join(REFERENCE_DIR, ref_file)
                break
        if not ref_path or not os.path.exists(ref_path):
            print(f"找不到對應標準答案：{transcript_base}")
            continue

        optimized_text = load_text(opt_path)
        reference_text = load_text(ref_path)
        score = simple_similarity(optimized_text, reference_text)
        results.append({
            "optimized_file": os.path.basename(opt_path),
            "reference_file": os.path.basename(ref_path),
            "similarity_score": score
        })
        print(f"{opt_name}: 相似度 {score:.4f}")

    # 輸出報表
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("optimized_file,reference_file,similarity_score\n")
        for r in results:
            f.write(f"{r['optimized_file']},{r['reference_file']},{r['similarity_score']:.4f}\n")
    print(f"\n評估報表已產生：{REPORT_PATH}")

if __name__ == "__main__":
    main()