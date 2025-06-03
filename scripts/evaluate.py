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

# 強制 transformers/bert-score 只用本地模型
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# 導入新的評估模組
try:
    from evaluation import MeetingEvaluator, EvaluationConfig
    EVALUATOR_AVAILABLE = True
except ImportError as e:
    print(f"警告: 無法載入多指標評估模組: {str(e)}")
    print("將使用舊版評估方法。請確保已安裝所有依賴項。")
    EVALUATOR_AVAILABLE = False
    MeetingEvaluator = None
    EvaluationConfig = None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='評估優化後的會議記錄')
    parser.add_argument('--model', type=str, default=None,
                      help='只評估指定模型的結果，例如：gemma3_4b')
    parser.add_argument('--all-models', action='store_true',
                      help='評估所有模型的結果（與 run_all_models.sh 配合使用）')
    parser.add_argument('--use-legacy', action='store_true',
                      help='使用舊版評估方法（僅用於比較）')
    parser.add_argument('--report-dir', type=str, default=None,
                      help='自定義報告輸出目錄')
    return parser.parse_args()

# 評估指標相關（舊版兼容）
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

# 初始化新的評估器
evaluator = None
if EVALUATOR_AVAILABLE and MeetingEvaluator is not None:
    try:
        evaluator = MeetingEvaluator()
        print("已載入多指標評估系統")
    except Exception as e:
        print(f"警告: 無法初始化評估器: {str(e)}")
        print("將使用舊版評估方法")
        evaluator = None
else:
    print("警告: 將使用舊版評估方法")

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
    """離線 BERTScore 計算，使用本地快取模型"""
    try:
        from bert_score import BERTScorer
    except ImportError:
        print("警告: bert-score 未安裝，跳過 BERTScore 計算")
        return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}
    
    try:
        # 使用全局 scorer 實例，確保模型只下載一次並離線快取
        global _bert_offline_scorer
        if '_bert_offline_scorer' not in globals():
            _bert_offline_scorer = BERTScorer(lang="zh", rescale_with_baseline=True, device="cpu")
        
        scores = _bert_offline_scorer.score(predictions, references)
        
        # 安全地處理返回值，避免類型檢查錯誤
        def safe_extract_score(score_value):
            """安全地從各種格式中提取數值分數"""
            try:
                # 如果是 tensor 且有 mean 方法
                if hasattr(score_value, 'mean'):
                    mean_val = score_value.mean()
                    # 如果有 item 方法（PyTorch tensor）
                    if hasattr(mean_val, 'item'):
                        return float(mean_val.item())
                    else:
                        return float(mean_val)
                # 如果是數字
                elif isinstance(score_value, (int, float)):
                    return float(score_value)
                # 如果是列表或數組，取第一個元素
                elif hasattr(score_value, '__getitem__') and len(score_value) > 0:
                    return float(score_value[0])
                else:
                    return 0.0
            except Exception:
                return 0.0
        
        # 檢查返回值類型並處理
        if isinstance(scores, tuple) and len(scores) == 3:
            P, R, F1 = scores
            return {
                "bertscore_precision": safe_extract_score(P),
                "bertscore_recall": safe_extract_score(R),
                "bertscore_f1": safe_extract_score(F1)
            }
        else:
            # 如果返回格式不是預期的tuple，使用默認值
            return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}
            
    except Exception as e:
        print(f"BERTScore 離線計算錯誤: {str(e)}")
        return {"bertscore_precision": 0.0, "bertscore_recall": 0.0, "bertscore_f1": 0.0}

def calculate_rouge(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """舊版 ROUGE 計算（兼容用）"""
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
    """簡單文本相似度計算"""
    return difflib.SequenceMatcher(None, a, b).ratio()

def evaluate_with_metrics(pred_text: str, ref_text: str, use_legacy: bool = False, verbose: bool = True) -> Dict[str, float]:
    """
    使用多指標評估系統評估文本
    
    Args:
        pred_text: 預測文本
        ref_text: 參考文本
        use_legacy: 是否使用舊版評估方法
        verbose: 是否輸出詳細日誌
        
    Returns:
        包含所有評估指標的字典
    """
    if not pred_text or not ref_text:
        if verbose:
            print("錯誤：評估文本或參考文本為空")
        return {
            'overall_score': 0.0,
            'semantic_similarity': 0.0,
            'content_coverage': 0.0,
            'structure_quality': 0.0,
            'weighted_score': 0.0
        }
    
    if use_legacy:
        # 使用舊版評估方法
        if verbose:
            print("使用舊版評估方法...")
            
        metrics = {}
        
        try:
            # 計算簡單相似度
            metrics['simple_similarity'] = simple_similarity(pred_text, ref_text)
            
            # 計算 BERTScore
            bert_scores = calculate_bertscore([pred_text], [ref_text])
            metrics.update(bert_scores)
            
            # 計算 ROUGE 分數
            rouge_scores = calculate_rouge([pred_text], [ref_text])
            metrics.update(rouge_scores)
            
            # 計算加權分數
            weights = {
                'simple_similarity': 0.2,
                'bertscore_f1': 0.5,
                'rouge_rougeL': 0.3
            }
            
            metrics['weighted_score'] = sum(metrics.get(k, 0) * weights.get(k, 0) for k in weights)
            return metrics
            
        except Exception as e:
            if verbose:
                print(f"舊版評估出錯: {str(e)}")
            return {
                'overall_score': 0.0,
                'semantic_similarity': 0.0,
                'content_coverage': 0.0,
                'structure_quality': 0.0,
                'weighted_score': 0.0
            }
    else:
        # 使用新版多指標評估系統
        if verbose:
            print("使用新版多指標評估系統...")
        
        # 檢查 evaluator 是否可用
        if evaluator is None:
            if verbose:
                print("評估器未初始化，回退到舊版方法")
            return evaluate_with_metrics(pred_text, ref_text, use_legacy=True, verbose=verbose)
            
        try:
            result = evaluator.evaluate(ref_text, pred_text)
            
            if not result or 'scores' not in result:
                if verbose:
                    print("評估結果格式不正確")
                return {
                    'overall_score': 0.0,
                    'semantic_similarity': 0.0,
                    'content_coverage': 0.0,
                    'structure_quality': 0.0,
                    'weighted_score': 0.0
                }
            
            # 將結果轉換為與舊版兼容的格式
            metrics = {
                'overall_score': float(result.get('overall_score', 0.0)),
                'semantic_similarity': float(result.get('scores', {}).get('semantic_similarity', {}).get('_weighted', 0.0)),
                'content_coverage': float(result.get('scores', {}).get('content_coverage', {}).get('_weighted', 0.0)),
                'structure_quality': float(result.get('scores', {}).get('structure_quality', {}).get('_weighted', 0.0)),
                'weighted_score': float(result.get('overall_score', 0.0)),
                'details': result.get('details', {})
            }
            return metrics
        except Exception as e:
            if verbose:
                print(f"新版多指標評估系統出錯: {str(e)}，回退到舊版方法")
            return evaluate_with_metrics(pred_text, ref_text, use_legacy=True, verbose=verbose)

def evaluate_texts(pred_text: str, ref_text: str, use_legacy: bool = False) -> Dict[str, float]:
    """
    評估文本對
    
    Args:
        pred_text: 預測文本
        ref_text: 參考文本
        use_legacy: 是否使用舊版評估方法
        
    Returns:
        包含評估指標的字典
    """
    return evaluate_with_metrics(pred_text, ref_text, use_legacy)

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

def main():
    args = parse_arguments()
    
    # 設置報告目錄
    report_dir = args.report_dir or REPORT_DIR
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(OPTIMIZED_DIR, exist_ok=True)
    
    print(f"使用評估模式: {'舊版' if (args.use_legacy or not EVALUATOR_AVAILABLE) else '新版多指標'}")
    print(f"報告將保存至: {os.path.abspath(report_dir)}")
    
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
    
    def print_metrics(metrics_dict: Dict[str, Dict[str, List[Any]]], title: str) -> None:
        print(f"\n=== {title} ===")
        for name, metrics in metrics_dict.items():
            print(f"\n{name}")
            print("-" * 50)
            for metric_name, values in metrics.items():
                if not values:
                    continue
                    
                # 過濾掉非數值類型的值
                numeric_values = []
                for v in values:
                    if isinstance(v, (int, float)):
                        numeric_values.append(v)
                    elif isinstance(v, dict) and 'f1' in v:  # 如果是包含 'f1' 的字典，使用 f1 值
                        numeric_values.append(v['f1'])
                
                if numeric_values:  # 只有在有有效數值時才計算平均
                    avg = sum(numeric_values) / len(numeric_values)
                    print(f"{metric_name}: {avg:.4f}")
                else:
                    print(f"{metric_name}: 無有效數值")
    
    print_metrics(dict(model_metrics), "模型評估結果")
    print_metrics(dict(strategy_metrics), "策略評估結果")
    
    detailed_results = {}
    for base_name, models in results.items():
        detailed_results[base_name] = {}
        for model, strategies in models.items():
            detailed_results[base_name][model] = {}
            for strategy, metrics in strategies.items():
                detailed_results[base_name][model][strategy] = {}
                for k, v in metrics.items():
                    try:
                        # 嘗試轉換為 Python 原生類型，以確保 JSON 序列化
                        detailed_results[base_name][model][strategy][k] = float(v) if isinstance(v, (int, float, bool)) else str(v)
                    except (ValueError, TypeError):
                        # 如果轉換失敗，轉為字符串
                        detailed_results[base_name][model][strategy][k] = str(v)
    
    def calculate_averages(metrics_dict):
        """計算指標平均值，處理可能包含字典的值"""
        averages = {}
        for name, metrics in metrics_dict.items():
            averages[name] = {}
            for metric_name, values in metrics.items():
                if not values:
                    averages[name][metric_name] = None
                    continue
                    
                # 過濾出數值或包含 'f1' 鍵的字典
                numeric_values = []
                for v in values:
                    if isinstance(v, (int, float)):
                        numeric_values.append(v)
                    elif isinstance(v, dict) and 'f1' in v:
                        numeric_values.append(v['f1'])
                
                if numeric_values:
                    averages[name][metric_name] = float(sum(numeric_values) / len(numeric_values))
                else:
                    averages[name][metric_name] = None
        return averages
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "evaluation_time_seconds": evaluation_time,
        "files_processed": processed_count,
        "models_evaluated": list(model_metrics.keys()),
        "strategies_evaluated": list(strategy_metrics.keys()),
        "metrics_used": ["simple_similarity", "bertscore_f1", "rouge_rougeL", "weighted_score"],
        "detailed_results": detailed_results,
        "model_averages": calculate_averages(model_metrics),
        "strategy_averages": calculate_averages(strategy_metrics)
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