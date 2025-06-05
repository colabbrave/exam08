import re
import argparse
import statistics
from typing import List

def parse_log(file_path: str) -> List[float]:
    """
    解析 log 檔並擷取所有品質分數 (假設每行格式為 '品質分數: <number>')
    """
    quality_scores = []
    pattern = re.compile(r"品質分數\s*[:=]\s*(\d+\.?\d*)")
    try:
        with open(file_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                match = pattern.search(line)
                if match:
                    score = float(match.group(1))
                    quality_scores.append(score)
    except FileNotFoundError:
        print(f"檔案 {file_path} 不存在")
    except Exception as e:
        print(f"發生錯誤: {e}")
    return quality_scores

def analyze_trend(quality_scores: List[float]) -> None:
    """
    根據品質分數計算並輸出異動趨勢與統計數據
    """
    if not quality_scores:
        print("無法取得品質分數資料。")
        return

    # 計算每次變化的差異值
    changes = [b - a for a, b in zip(quality_scores, quality_scores[1:])]
    overall_change = quality_scores[-1] - quality_scores[0]

    print("品質分數異動趨勢分析:")
    print(f"初始品質分數: {quality_scores[0]}")
    print(f"最新品質分數: {quality_scores[-1]}")
    print(f"整體品質分數變化: {overall_change:.2f}")

    if changes:
        avg_change = statistics.mean(changes)
        print(f"每次平均變化值: {avg_change:.2f}")
        if avg_change > 0:
            print("趨勢：整體上升")
        elif avg_change < 0:
            print("趨勢：整體下降")
        else:
            print("趨勢：持平")
    else:
        print("品質分數資料不足，無法分析每次變化。")

def main() -> None:
    parser = argparse.ArgumentParser(description="分析 log 中的品質分數異動趨勢")
    parser.add_argument("log_file", help="log 檔案路徑")
    args = parser.parse_args()

    quality_scores = parse_log(args.log_file)
    analyze_trend(quality_scores)

if __name__ == "__main__":
    main()