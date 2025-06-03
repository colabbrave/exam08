#!/usr/bin/env python3
"""
會議記錄優化系統 - 綜合性能評估報告
分析整個系統的優化效果、問題診斷與改進建議
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import re

def load_all_scores():
    """載入所有會議的疊代分數"""
    results = {}
    iterations_dir = Path('results/iterations')
    
    if not iterations_dir.exists():
        return results
    
    for meeting_dir in iterations_dir.iterdir():
        if meeting_dir.is_dir() and not meeting_dir.name.startswith('tmp'):
            meeting_name = meeting_dir.name
            scores = []
            
            score_files = sorted([f for f in meeting_dir.glob('iteration_*_scores.json')], 
                               key=lambda x: int(x.stem.split('_')[1]))
            
            for score_file in score_files:
                try:
                    with open(score_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        iteration = int(score_file.stem.split('_')[1])
                        
                        if 'scores' in data and 'overall_score' in data['scores']:
                            score = data['scores']['overall_score']
                            strategy = data.get('strategy_combination', [])
                            scores.append({
                                'iteration': iteration,
                                'score': score,
                                'strategy': strategy,
                                'execution_time': data.get('execution_time', 0)
                            })
                except Exception as e:
                    print(f'警告: 無法讀取 {score_file}: {e}')
            
            if scores:
                results[meeting_name] = scores
    
    return results

def analyze_early_stopping_effectiveness():
    """分析 early stopping 機制的有效性"""
    all_scores = load_all_scores()
    analysis = {}
    
    for meeting, scores in all_scores.items():
        if len(scores) < 3:
            continue
            
        score_values = [s['score'] for s in scores]
        
        # 計算改進趨勢
        improvements = []
        for i in range(1, len(score_values)):
            improvements.append(score_values[i] - score_values[i-1])
        
        # 找到最後有效改進
        significant_improvements = [i for i, imp in enumerate(improvements) if imp > 0.01]
        last_improvement_idx = significant_improvements[-1] if significant_improvements else 0
        
        # 分析是否應該更早停止
        should_stop_at = last_improvement_idx + 3  # patience = 3
        actual_iterations = len(scores)
        
        analysis[meeting] = {
            'actual_iterations': actual_iterations,
            'should_stop_at': min(should_stop_at, actual_iterations),
            'wasted_iterations': max(0, actual_iterations - should_stop_at),
            'last_significant_improvement': last_improvement_idx,
            'final_score': score_values[-1],
            'best_score': max(score_values),
            'best_iteration': score_values.index(max(score_values)),
            'efficiency_ratio': should_stop_at / actual_iterations if actual_iterations > 0 else 0
        }
    
    return analysis

def analyze_strategy_effectiveness():
    """分析策略組合的有效性"""
    all_scores = load_all_scores()
    strategy_performance = {}
    
    for meeting, scores in all_scores.items():
        for score_data in scores:
            strategies = tuple(sorted(score_data['strategy']))
            score = score_data['score']
            
            if strategies not in strategy_performance:
                strategy_performance[strategies] = []
            strategy_performance[strategies].append(score)
    
    # 計算每個策略組合的統計
    strategy_stats = {}
    for strategies, scores in strategy_performance.items():
        if len(scores) >= 2:  # 至少要有2次使用
            strategy_stats[strategies] = {
                'avg_score': np.mean(scores),
                'std_score': np.std(scores),
                'usage_count': len(scores),
                'max_score': max(scores),
                'min_score': min(scores)
            }
    
    # 排序找出最佳策略
    best_strategies = sorted(strategy_stats.items(), 
                           key=lambda x: x[1]['avg_score'], 
                           reverse=True)
    
    return strategy_stats, best_strategies

def analyze_execution_performance():
    """分析執行性能"""
    all_scores = load_all_scores()
    performance_stats = {}
    
    for meeting, scores in all_scores.items():
        execution_times = [s['execution_time'] for s in scores if s['execution_time'] > 0]
        
        if execution_times:
            performance_stats[meeting] = {
                'avg_time_per_iteration': np.mean(execution_times),
                'total_time': sum(execution_times),
                'min_time': min(execution_times),
                'max_time': max(execution_times),
                'time_efficiency': np.mean(execution_times) / 60  # 分鐘為單位
            }
    
    return performance_stats

def generate_comprehensive_report():
    """生成綜合評估報告"""
    print("=" * 100)
    print("會議記錄優化系統 - 綜合性能評估報告")
    print("=" * 100)
    print(f"評估時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"評估範圍: 完整系統運行歷史記錄")
    print()
    
    # 載入基本統計
    all_scores = load_all_scores()
    
    print("📊 系統概覽")
    print("-" * 50)
    total_meetings = len(all_scores)
    total_iterations = sum(len(scores) for scores in all_scores.values())
    print(f"   • 處理會議數量: {total_meetings} 場")
    print(f"   • 總疊代次數: {total_iterations} 輪")
    
    if total_iterations > 0:
        avg_iterations = total_iterations / total_meetings
        print(f"   • 平均疊代次數: {avg_iterations:.1f} 輪/會議")
    print()
    
    # Early Stopping 分析
    print("🛑 Early Stopping 機制分析")
    print("-" * 50)
    es_analysis = analyze_early_stopping_effectiveness()
    
    total_wasted = sum(a['wasted_iterations'] for a in es_analysis.values())
    avg_efficiency = np.mean([a['efficiency_ratio'] for a in es_analysis.values()])
    
    print(f"   • 總浪費疊代次數: {total_wasted} 輪")
    print(f"   • 平均效率比率: {avg_efficiency:.2%}")
    
    for meeting, analysis in es_analysis.items():
        meeting_short = meeting[:15] + "..." if len(meeting) > 15 else meeting
        print(f"   • {meeting_short}:")
        print(f"     - 實際疊代: {analysis['actual_iterations']} 輪")
        print(f"     - 建議停止於: 第{analysis['should_stop_at']} 輪")
        print(f"     - 浪費疊代: {analysis['wasted_iterations']} 輪")
        print(f"     - 最佳分數在: 第{analysis['best_iteration']} 輪 ({analysis['best_score']:.4f})")
    print()
    
    # 策略效果分析
    print("🎯 策略組合效果分析")
    print("-" * 50)
    strategy_stats, best_strategies = analyze_strategy_effectiveness()
    
    print(f"   • 總測試策略組合: {len(strategy_stats)} 種")
    print(f"   • 有效策略組合 (>=2次使用): {len(best_strategies)} 種")
    print()
    print("   🏆 前5名最佳策略組合:")
    
    for i, (strategies, stats) in enumerate(best_strategies[:5]):
        strategy_names = [s.split('_')[-1] for s in strategies]
        print(f"   {i+1}. {' + '.join(strategy_names)}")
        print(f"      平均分數: {stats['avg_score']:.4f} (±{stats['std_score']:.4f})")
        print(f"      使用次數: {stats['usage_count']} 次")
        print(f"      分數範圍: {stats['min_score']:.4f} ~ {stats['max_score']:.4f}")
    print()
    
    # 執行性能分析
    print("⚡ 執行性能分析")
    print("-" * 50)
    perf_stats = analyze_execution_performance()
    
    if perf_stats:
        avg_times = [stats['avg_time_per_iteration'] for stats in perf_stats.values()]
        total_times = [stats['total_time'] for stats in perf_stats.values()]
        
        print(f"   • 平均每輪耗時: {np.mean(avg_times):.1f} 秒")
        print(f"   • 平均總處理時間: {np.mean(total_times)/60:.1f} 分鐘/會議")
        print(f"   • 最快處理時間: {min(total_times)/60:.1f} 分鐘")
        print(f"   • 最慢處理時間: {max(total_times)/60:.1f} 分鐘")
    print()
    
    # 問題診斷
    print("🔍 問題診斷")
    print("-" * 50)
    
    major_issues = []
    
    # 檢查過度疊代
    if total_wasted > total_iterations * 0.3:
        major_issues.append("❌ 嚴重的過度疊代問題")
        print("   ❌ 嚴重的過度疊代問題")
        print("      - 超過30%的疊代是不必要的")
        print("      - early stopping 機制需要調整")
    
    # 檢查分數波動
    volatile_meetings = []
    for meeting, scores in all_scores.items():
        score_values = [s['score'] for s in scores]
        if len(score_values) > 3:
            volatility = np.std(score_values)
            if volatility > 0.15:
                volatile_meetings.append((meeting, volatility))
    
    if len(volatile_meetings) > 0:
        major_issues.append("❌ 分數波動過大")
        print("   ❌ 分數波動過大")
        print("      - 以下會議分數不穩定:")
        for meeting, vol in volatile_meetings[:3]:
            meeting_short = meeting[:20] + "..." if len(meeting) > 20 else meeting
            print(f"        • {meeting_short}: σ={vol:.4f}")
    
    # 檢查整體改善效果
    improvement_rates = []
    for meeting, scores in all_scores.items():
        if len(scores) >= 2:
            score_values = [s['score'] for s in scores]
            improvement = (score_values[-1] - score_values[0]) / score_values[0]
            improvement_rates.append(improvement)
    
    if improvement_rates:
        avg_improvement = np.mean(improvement_rates)
        if avg_improvement < 0:
            major_issues.append("❌ 整體品質下降")
            print("   ❌ 整體品質下降")
            print(f"      - 平均改善率: {avg_improvement:.2%}")
            print("      - 系統可能存在根本性問題")
    
    if not major_issues:
        print("   ✅ 未發現重大問題")
    print()
    
    # 改進建議
    print("💡 系統改進建議")
    print("-" * 50)
    
    priority_suggestions = []
    
    if total_wasted > total_iterations * 0.2:
        priority_suggestions.append({
            'priority': '高',
            'category': '效率優化',
            'suggestion': '調整 early stopping 參數',
            'details': [
                '將 patience 設為 3-5 輪',
                '提高 min_improvement 閾值至 0.01',
                '添加連續下降檢測機制'
            ]
        })
    
    if len(volatile_meetings) > 0:
        priority_suggestions.append({
            'priority': '高',
            'category': '穩定性改善',
            'suggestion': '優化評估指標',
            'details': [
                '檢查 BERTScore 計算的一致性',
                '考慮使用多指標加權平均',
                '添加分數平滑機制'
            ]
        })
    
    if avg_improvement < 0:
        priority_suggestions.append({
            'priority': '緊急',
            'category': '策略優化',
            'suggestion': '重新設計策略選擇機制',
            'details': [
                '分析 LLM 改進建議的品質',
                '優化策略組合邏輯',
                '添加策略效果預測機制'
            ]
        })
    
    # 根據最佳策略提供建議
    if best_strategies:
        top_strategy = best_strategies[0][0]
        priority_suggestions.append({
            'priority': '中',
            'category': '策略應用',
            'suggestion': '優先使用高效策略組合',
            'details': [
                f'推薦使用: {" + ".join([s.split("_")[-1] for s in top_strategy])}',
                f'該組合平均分數: {best_strategies[0][1]["avg_score"]:.4f}',
                '考慮設為預設策略組合'
            ]
        })
    
    for i, suggestion in enumerate(priority_suggestions, 1):
        print(f"{i}. [{suggestion['priority']}優先級] {suggestion['category']}: {suggestion['suggestion']}")
        for detail in suggestion['details']:
            print(f"   • {detail}")
        print()
    
    # 建議系統參數調整
    print("⚙️  建議系統參數調整")
    print("-" * 50)
    
    # 基於分析結果計算建議參數
    if es_analysis:
        avg_best_iteration = np.mean([a['best_iteration'] for a in es_analysis.values()])
        suggested_patience = max(3, int(avg_best_iteration * 0.3))
        
        print("config/system_config.json 建議修改:")
        print(f'  "patience": {min(suggested_patience, 8)},')
        print(f'  "min_improvement": 0.01,')
        print(f'  "quality_threshold": 0.6,')
        print(f'  "max_iterations": {int(avg_best_iteration * 1.5)},')
    
    return {
        'total_meetings': total_meetings,
        'total_iterations': total_iterations,
        'early_stopping_analysis': es_analysis,
        'strategy_analysis': strategy_stats,
        'performance_analysis': perf_stats,
        'major_issues': major_issues,
        'suggestions': priority_suggestions
    }

if __name__ == "__main__":
    # 確保在正確的工作目錄
    if not os.path.exists('results/iterations'):
        print("錯誤: 未找到 results/iterations 目錄")
        print("請確保在專案根目錄執行此腳本")
        exit(1)
    
    # 執行綜合分析
    analysis_results = generate_comprehensive_report()
    
    # 保存分析結果 (轉換策略分析的tuple keys為字符串)
    analysis_results_serializable = analysis_results.copy()
    if 'strategy_analysis' in analysis_results_serializable:
        strategy_analysis_str = {}
        for k, v in analysis_results_serializable['strategy_analysis'].items():
            key_str = ' + '.join(k) if isinstance(k, tuple) else str(k)
            strategy_analysis_str[key_str] = v
        analysis_results_serializable['strategy_analysis'] = strategy_analysis_str
    
    with open('results/comprehensive_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results_serializable, f, ensure_ascii=False, indent=2, default=str)
    
    print("✅ 綜合評估完成！")
    print("📁 分析結果已保存至: results/comprehensive_analysis.json")
