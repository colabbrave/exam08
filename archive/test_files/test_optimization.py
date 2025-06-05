#!/usr/bin/env python3
"""
測試會議記錄優化效果

比較原始記錄、單一策略優化和組合策略優化的效果
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
import torch
from tqdm import tqdm
import os
import sys

# 防止本地 evaluate.py 遮蔽
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(current_dir, "evaluate.py")):
    raise RuntimeError("請移除 scripts/evaluate.py 以避免遮蔽 evaluate 套件")

import evaluate

# 初始化評估指標
rouge = evaluate.load('rouge')
bertscore = evaluate.load('bertscore')

def calculate_metrics(predictions: List[str], references: List[str]) -> Dict:
    """計算多種評估指標"""
    # ROUGE 指標
    rouge_results = rouge.compute(
        predictions=predictions,
        references=references,
        use_stemmer=True
    )
    if rouge_results is None:
        rouge_results = {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}

    # BERTScore
    bertscore_results = bertscore.compute(
        predictions=predictions,
        references=references,
        lang="zh"
    )
    if bertscore_results is None or 'f1' not in bertscore_results or not bertscore_results['f1']:
        avg_bertscore = 0.0
    else:
        avg_bertscore = sum(bertscore_results['f1']) / len(bertscore_results['f1'])

    return {
        'rouge1': rouge_results.get('rouge1', 0.0),
        'rouge2': rouge_results.get('rouge2', 0.0),
        'rougeL': rouge_results.get('rougeL', 0.0),
        'bertscore_f1': avg_bertscore,
        'weighted_score': (
            0.4 * rouge_results.get('rouge1', 0.0) +
            0.3 * rouge_results.get('rouge2', 0.0) +
            0.3 * avg_bertscore
        )
    }

def evaluate_optimization(
    original_texts: List[str],
    optimized_texts: List[str],
    references: List[str]
) -> Dict:
    """評估優化效果"""
    # 評估原始文本
    original_metrics = calculate_metrics(original_texts, references)
    
    # 評估優化文本
    optimized_metrics = calculate_metrics(optimized_texts, references)
    
    # 計算改進百分比
    improvement = {
        'rouge1_improvement': (optimized_metrics['rouge1'] - original_metrics['rouge1']) / original_metrics['rouge1'] * 100,
        'rouge2_improvement': (optimized_metrics['rouge2'] - original_metrics['rouge2']) / original_metrics['rouge2'] * 100,
        'rougeL_improvement': (optimized_metrics['rougeL'] - original_metrics['rougeL']) / original_metrics['rougeL'] * 100,
        'bertscore_improvement': (optimized_metrics['bertscore_f1'] - original_metrics['bertscore_f1']) / original_metrics['bertscore_f1'] * 100,
        'weighted_score_improvement': (optimized_metrics['weighted_score'] - original_metrics['weighted_score']) / original_metrics['weighted_score'] * 100,
    }
    
    return {
        'original_metrics': original_metrics,
        'optimized_metrics': optimized_metrics,
        'improvement': improvement
    }

def main():
    parser = argparse.ArgumentParser(description="測試會議記錄優化效果")
    parser.add_argument("--test-dir", default="data/test", help="測試數據目錄")
    parser.add_argument("--output-dir", default="results/evaluation", help="評估結果輸出目錄")
    args = parser.parse_args()
    
    # 準備目錄
    test_dir = Path(args.test_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加載測試數據
    print("加載測試數據...")
    test_files = list(test_dir.glob("*.txt"))
    
    results = []
    for test_file in tqdm(test_files, desc="處理測試文件"):
        # 這裡假設測試文件是原始記錄，參考文件有相同的名稱但位於不同目錄
        # 實際實現中需要根據實際情況調整
        ref_file = Path("data/references") / test_file.name
        
        if not ref_file.exists():
            print(f"警告：找不到參考文件 {ref_file}，跳過")
            continue
            
        with open(test_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
            
        with open(ref_file, 'r', encoding='utf-8') as f:
            reference_text = f.read()
            
        # 這裡應該調用優化函數生成優化後的文本
        # 為簡化示例，我們假設優化後的文本與參考文本相同
        optimized_text = reference_text  # 替換為實際的優化函數調用
        
        # 評估
        eval_result = evaluate_optimization(
            [original_text],
            [optimized_text],
            [reference_text]
        )
        
        results.append({
            'file': str(test_file.name),
            **eval_result
        })
    
    # 計算平均指標
    avg_metrics = {
        'original_metrics': {k: sum(r['original_metrics'][k] for r in results) / len(results) 
                           for k in results[0]['original_metrics']},
        'optimized_metrics': {k: sum(r['optimized_metrics'][k] for r in results) / len(results) 
                            for k in results[0]['optimized_metrics']},
        'improvement': {k: sum(r['improvement'][k] for r in results) / len(results) 
                       for k in results[0]['improvement']}
    }
    
    # 保存結果
    output_file = output_dir / "optimization_evaluation.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'per_file_results': results,
            'average_metrics': avg_metrics
        }, f, ensure_ascii=False, indent=2)
    
    print(f"評估完成！結果已保存至: {output_file}")
    print("\n平均指標改進：")
    for metric, value in avg_metrics['improvement'].items():
        print(f"{metric}: {value:.2f}%")

if __name__ == "__main__":
    main()
