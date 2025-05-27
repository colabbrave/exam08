import os
import re
import json
import time
import torch
import argparse
from glob import glob
from pathlib import Path
import difflib
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='評估優化後的會議記錄')
    parser.add_argument('--model', type=str, default=None,
                      help='只評估指定模型的結果，例如：gemma3_4b')
    parser.add_argument('--all-models', action='store_true',
                      help='評估所有模型的結果（與 run_all_models.sh 配合使用）')
    return parser.parse_args()

# 評估指標相關
try:
    from bert_score import score as bert_score
except ImportError:
    print("警告: 未安裝 bert-score，請執行 'pip install bert-score'")
    bert_score = None

try:
    from rouge_score import rouge_scorer, scoring
except ImportError:
    print("警告: 未安裝 rouge-score，請執行 'pip install rouge-score")
    rouge_scorer = None

# 類型別名
ScoreDict = Dict[str, float]
EvaluationResult = Dict[str, Dict[str, Dict[str, float]]]

# 使用絕對路徑避免相對路徑問題
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

REFERENCE_DIR = os.path.join(ROOT_DIR, "data/reference")
OPTIMIZED_DIR = os.path.join(ROOT_DIR, "results/optimized")
REPORT_DIR = os.path.join(ROOT_DIR, "results/evaluation_reports")

def load_text(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

def calculate_bertscore(predictions: List[str], references: List[str]) -> Dict[str, float]:
    if bert_score is None:
        print("警告: bert-score 未安裝，跳過 BERTScore 計算")
        return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}
    
    try:
        P, R, F1 = bert_score(
            predictions,
            references,
            lang="zh",
            verbose=True,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        return {
            "bertscore_precision": float(P.mean().item()),
            "bertscore_recall": float(R.mean().item()),
            "bertscore_f1": float(F1.mean().item())
        }
    except Exception as e:
        print(f"BERTScore 計算錯誤: {str(e)}")
        return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}

def calculate_rouge(predictions: List[str], references: List[str]) -> Dict[str, float]:
    if rouge_scorer is None:
        print("警告: rouge-score 未安裝，跳過 ROUGE 計算")
        return {"rouge_rouge1": 0.0, "rouge_rouge2": 0.0, "rouge_rougeL": 0.0}
    
    try:
        scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=True
        )
        
        scores = []
        for ref, pred in zip(references, predictions):
            scores.append(scorer.score(ref, pred))
        
        avg_scores = {}
        for key in scores[0]:
            avg_scores[f"rouge_{key}"] = float(sum(s[key].fmeasure for s in scores) / len(scores))
        
        return avg_scores
    except Exception as e:
        print(f"ROUGE 計算錯誤: {str(e)}")
        return {"rouge_rouge1": 0.0, "rouge_rouge2": 0.0, "rouge_rougeL": 0.0}

def simple_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_base_name(filename):
    # 匹配格式：第671次市政會議114年5月13日
    match = re.search(r'(第\d+次市政會議\d+年\d+月\d+日)', filename)
    if match:
        return match.group(1)
    # 如果沒有匹配到，嘗試提取基本名稱（去掉後綴）
    base = os.path.basename(filename)
    # 移除文件擴展名
    base = re.sub(r'\.[^.]+$', '', base)
    # 移除策略和模型名稱部分（如果有）
    base = re.sub(r'__[^_]+__[^_]+$', '', base)
    # 移除多餘的「逐字稿」或「會議紀錄」字樣
    base = base.replace("逐字稿", "").replace("會議紀錄", "").strip()
    return base

def extract_model_name(filename):
    match = re.search(r'__([^_].*?)(?:\.\w+)?$', filename)
    if match:
        model_name = match.group(1).strip()
        if 'llama3-taide' in model_name:
            parts = model_name.split('_')
            if len(parts) > 2 and 'llama3-taide' in parts[1]:
                return f"{parts[0]}/{parts[1]}_{parts[2]}"
        return model_name
    return "unknown_model"

def extract_strategy_name(filename):
    parts = [p for p in filename.split('__') if p]
    if len(parts) >= 3:
        return parts[-2]
    return "unknown_strategy"

def evaluate_texts(pred_text: str, ref_text: str) -> Dict[str, float]:
    metrics = {
        'simple_similarity': simple_similarity(pred_text, ref_text)
    }
    
    bert_scores = calculate_bertscore([pred_text], [ref_text])
    metrics.update(bert_scores)
    
    rouge_scores = calculate_rouge([pred_text], [ref_text])
    metrics.update(rouge_scores)
    
    weights = {
        'simple_similarity': 0.2,
        'bertscore_f1': 0.5,
        'rouge_rougeL': 0.3
    }
    
    weighted_score = sum(metrics[k] * weights.get(k, 0) for k in weights)
    metrics['weighted_score'] = weighted_score
    
    return metrics

def main():
    args = parse_arguments()
    
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(OPTIMIZED_DIR, exist_ok=True)
    
    reference_files = glob(f"{REFERENCE_DIR}/*.txt") + glob(f"{REFERENCE_DIR}/*.md")
    if not reference_files:
        print(f"錯誤: 在 {REFERENCE_DIR} 中找不到參考文件")
        return
    
    results = defaultdict(lambda: defaultdict(dict))
    model_metrics = defaultdict(lambda: defaultdict(list))
    strategy_metrics = defaultdict(lambda: defaultdict(list))
    
    start_time = time.time()
    
    print(f"正在搜尋參考文件: {REFERENCE_DIR}/*.{{txt,md}}")
    reference_files = glob(f"{REFERENCE_DIR}/*.txt") + glob(f"{REFERENCE_DIR}/*.md")
    print(f"找到 {len(reference_files)} 個參考文件")
    
    print(f"\n正在搜尋優化文件: {OPTIMIZED_DIR}/**/*.{{txt,md}}")
    optimized_files = []
    for ext in ('*.txt', '*.md'):
        files = glob(f"{OPTIMIZED_DIR}/**/*{ext}", recursive=True)
        print(f"找到 {len(files)} 個 {ext} 文件")
        optimized_files.extend(files)
    
    # 過濾掉可能的重複文件
    optimized_files = list(dict.fromkeys(optimized_files))
    
    if not optimized_files:
        print(f"錯誤: 在 {OPTIMIZED_DIR} 中找不到優化後的文件")
        return
    
    processed_count = 0
    for opt_path in optimized_files:
        try:
            opt_name = Path(opt_path).name
            model_name = extract_model_name(opt_name)
            
            # 添加模型過濾邏輯
            if args.model and not args.all_models and args.model.lower() not in model_name.lower():
                continue
                
            strategy_name = extract_strategy_name(opt_name)
            base_name = get_base_name(opt_name)
            
            ref_path = None
            base_name_clean = get_base_name(opt_name)
            
            for ref_file in reference_files:
                ref_base = get_base_name(ref_file)
                if base_name_clean == ref_base:
                    ref_path = ref_file
                    break
            
            if not ref_path:
                for ref_file in reference_files:
                    ref_base = get_base_name(ref_file)
                    if ref_base in base_name_clean or base_name_clean in ref_base:
                        ref_path = ref_file
                        break
            
            if not ref_path:
                print(f"警告: 找不到 {opt_name} 的參考文件 (base: {base_name_clean})")
                print(f"可用的參考文件: {[get_base_name(f) for f in reference_files]}")
                continue
                
            optimized_text = load_text(opt_path)
            reference_text = load_text(ref_path)
            
            if not optimized_text or not reference_text:
                print(f"警告: {opt_name} 或參考文件為空")
                continue
            
            metrics = evaluate_texts(optimized_text, reference_text)
            
            results[base_name][model_name][strategy_name] = metrics
            
            for metric_name, value in metrics.items():
                model_metrics[model_name][metric_name].append(value)
                strategy_metrics[strategy_name][metric_name].append(value)
            
            print(f"{opt_name}: 加權分數 {metrics.get('weighted_score', 0):.4f} (BERTScore F1: {metrics.get('bertscore_f1', 0):.4f}, ROUGE-L: {metrics.get('rouge_rougeL', 0):.4f})")
            processed_count += 1
            
        except Exception as e:
            print(f"處理 {opt_name} 時出錯: {str(e)}")
            continue
    
    if processed_count == 0:
        print("錯誤: 沒有處理任何文件，請檢查文件路徑和格式")
        return
    
    evaluation_time = time.time() - start_time
    
    print("\n=== 評估摘要 ===")
    print(f"處理文件數: {processed_count}")
    print(f"總用時: {evaluation_time:.2f} 秒")
    
    def print_metrics(metrics_dict: Dict[str, Dict[str, List[float]]], title: str) -> None:
        print(f"\n=== {title} ===")
        for name, metrics in metrics_dict.items():
            print(f"\n{name}")
            print("-" * 50)
            for metric_name, values in metrics.items():
                if values:
                    avg = sum(values) / len(values)
                    print(f"{metric_name}: {avg:.4f}")
    
    print_metrics(model_metrics, "模型評估結果")
    print_metrics(strategy_metrics, "策略評估結果")
    
    detailed_results = {}
    for base_name, models in results.items():
        detailed_results[base_name] = {}
        for model, strategies in models.items():
            detailed_results[base_name][model] = {}
            for strategy, metrics in strategies.items():
                detailed_results[base_name][model][strategy] = {
                    k: float(v) for k, v in metrics.items()
                }
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "evaluation_time_seconds": evaluation_time,
        "files_processed": processed_count,
        "models_evaluated": list(model_metrics.keys()),
        "strategies_evaluated": list(strategy_metrics.keys()),
        "metrics_used": ["simple_similarity", "bertscore_f1", "rouge_rougeL", "weighted_score"],
        "detailed_results": detailed_results,
        "model_averages": {
            model: {metric: float(sum(values)/len(values)) for metric, values in metrics.items()}
            for model, metrics in model_metrics.items()
        },
        "strategy_averages": {
            strategy: {metric: float(sum(values)/len(values)) for metric, values in metrics.items()}
            for strategy, metrics in strategy_metrics.items()
        }
    }
    
    report_path = os.path.join(REPORT_DIR, f"evaluation_report_{time.strftime('%Y%m%d_%H%M%S')}.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n評估完成！報告已保存至: {report_path}")
    except Exception as e:
        print(f"保存報告時出錯: {str(e)}")
        print("\n報告摘要:")
        print(json.dumps({
            "files_processed": report["files_processed"],
            "evaluation_time_seconds": report["evaluation_time_seconds"],
            "models": report["models_evaluated"],
            "strategies": report["strategies_evaluated"]
        }, indent=2))

if __name__ == "__main__":
    main()