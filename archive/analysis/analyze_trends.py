#!/usr/bin/env python3
"""
品質分數變動趨勢分析工具
分析會議記錄優化系統的效果
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
from datetime import datetime

def analyze_iteration_scores(meeting_folder):
    """分析單次會議的疊代分數變化"""
    iterations_dir = Path(f'results/iterations/{meeting_folder}')
    
    if not iterations_dir.exists():
        return [], {}
    
    scores = []
    score_files = sorted([f for f in iterations_dir.glob('iteration_*_scores.json')], 
                        key=lambda x: int(x.stem.split('_')[1]))
    
    for score_file in score_files:
        try:
            with open(score_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                iteration = int(score_file.stem.split('_')[1])
                
                # 提取總分
                total_score = None
                if 'scores' in data and 'overall_score' in data['scores']:
                    total_score = data['scores']['overall_score']
                elif 'overall_quality' in data:
                    total_score = data['overall_quality']
                elif 'quality_score' in data:
                    total_score = data['quality_score']
                
                if total_score is not None:
                    scores.append((iteration, total_score))
                    
        except Exception as e:
            print(f'警告: 無法讀取 {score_file}: {e}')
    
    # 分析統計資料
    if not scores:
        return [], {}
    
    iterations, score_values = zip(*scores)
    stats = {
        'total_iterations': len(scores),
        'initial_score': score_values[0],
        'final_score': score_values[-1],
        'max_score': max(score_values),
        'min_score': min(score_values),
        'max_iteration': iterations[score_values.index(max(score_values))],
        'min_iteration': iterations[score_values.index(min(score_values))],
        'improvement': score_values[-1] - score_values[0],
        'volatility': np.std(score_values),
        'trend': 'improving' if score_values[-1] > score_values[0] else 'declining'
    }
    
    return scores, stats

def create_trend_visualization():
    """創建品質趨勢視覺化圖表"""
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('會議記錄優化系統 - 品質分數變動趨勢分析', fontsize=16, fontweight='bold')
    
    meetings = ['第671次市政會議114年5月13日逐字稿', '第672次市政會議114年5月20日逐字稿']
    colors = ['#2E86AB', '#A23B72']
    
    all_stats = {}
    
    for idx, meeting in enumerate(meetings):
        scores, stats = analyze_iteration_scores(meeting)
        all_stats[meeting] = stats
        
        if not scores:
            continue
            
        iterations, score_values = zip(*scores)
        
        # 主要趨勢圖
        ax = axes[0, idx]
        ax.plot(iterations, score_values, color=colors[idx], linewidth=2, marker='o', markersize=4)
        ax.set_title(f'{meeting[:8]}...', fontsize=12, fontweight='bold')
        ax.set_xlabel('疊代次數')
        ax.set_ylabel('品質分數')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(1, max(score_values) * 1.1))
        
        # 添加關鍵點標註
        max_idx = score_values.index(max(score_values))
        ax.annotate(f'最高: {max(score_values):.4f}\n(第{iterations[max_idx]}輪)', 
                   xy=(iterations[max_idx], max(score_values)),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # 比較統計圖
    ax = axes[1, 0]
    meeting_names = [f'第{671+i}次' for i in range(len(all_stats))]
    metrics = ['initial_score', 'final_score', 'max_score']
    metric_labels = ['初始分數', '最終分數', '最高分數']
    
    x = np.arange(len(meeting_names))
    width = 0.25
    
    for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
        values = [all_stats[meeting][metric] for meeting in meetings if meeting in all_stats]
        ax.bar(x + i*width, values, width, label=label, alpha=0.8)
    
    ax.set_xlabel('會議')
    ax.set_ylabel('分數')
    ax.set_title('會議分數比較')
    ax.set_xticks(x + width)
    ax.set_xticklabels(meeting_names)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 改善效果分析
    ax = axes[1, 1]
    improvements = [all_stats[meeting]['improvement'] for meeting in meetings if meeting in all_stats]
    volatilities = [all_stats[meeting]['volatility'] for meeting in meetings if meeting in all_stats]
    
    colors_scatter = ['green' if imp > 0 else 'red' for imp in improvements]
    ax.scatter(improvements, volatilities, c=colors_scatter, s=100, alpha=0.7)
    
    for i, meeting in enumerate([m for m in meetings if m in all_stats]):
        ax.annotate(f'第{671+i}次', (improvements[i], volatilities[i]), 
                   xytext=(5, 5), textcoords='offset points')
    
    ax.set_xlabel('改善幅度 (最終-初始)')
    ax.set_ylabel('分數波動性 (標準差)')
    ax.set_title('改善效果 vs 穩定性')
    ax.grid(True, alpha=0.3)
    ax.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('results/quality_trends_analysis.png', dpi=300, bbox_inches='tight')
    print("圖表已保存至: results/quality_trends_analysis.png")
    
    return all_stats

def generate_analysis_report():
    """生成詳細的分析報告"""
    print("=" * 80)
    print("會議記錄優化系統 - 品質分數變動趨勢分析報告")
    print("=" * 80)
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    meetings = ['第671次市政會議114年5月13日逐字稿', '第672次市政會議114年5月20日逐字稿']
    
    for i, meeting in enumerate(meetings):
        print(f"{i+1}. {meeting}")
        print("-" * 60)
        
        scores, stats = analyze_iteration_scores(meeting)
        
        if not scores:
            print("   ⚠️  未找到有效的分數資料")
            continue
        
        print(f"   📊 疊代統計:")
        print(f"      • 總疊代次數: {stats['total_iterations']} 輪")
        print(f"      • 初始分數: {stats['initial_score']:.4f}")
        print(f"      • 最終分數: {stats['final_score']:.4f}")
        print(f"      • 最高分數: {stats['max_score']:.4f} (第{stats['max_iteration']}輪)")
        print(f"      • 最低分數: {stats['min_score']:.4f} (第{stats['min_iteration']}輪)")
        
        print(f"   📈 效果評估:")
        improvement = stats['improvement']
        if improvement > 0:
            print(f"      • ✅ 整體改善: +{improvement:.4f} ({improvement/stats['initial_score']*100:.1f}%)")
        else:
            print(f"      • ❌ 整體下降: {improvement:.4f} ({improvement/stats['initial_score']*100:.1f}%)")
        
        print(f"      • 穩定性 (波動度): {stats['volatility']:.4f}")
        print(f"      • 趨勢方向: {'📈 上升' if stats['trend'] == 'improving' else '📉 下降'}")
        
        # 分析異常情況
        if stats['total_iterations'] > 50:
            print(f"      • ⚠️  異常: 疊代次數過多 ({stats['total_iterations']} 輪)")
            print(f"         可能原因: early stopping 機制未正常運作")
        
        if stats['volatility'] > 0.1:
            print(f"      • ⚠️  異常: 分數波動過大 (σ={stats['volatility']:.4f})")
            print(f"         可能原因: 策略優化不穩定或評估指標波動")
        
        print()
    
    # 生成建議
    print("🔍 系統優化建議:")
    print("-" * 60)
    
    all_meetings_stats = {}
    for meeting in meetings:
        _, stats = analyze_iteration_scores(meeting)
        if stats:
            all_meetings_stats[meeting] = stats
    
    if len(all_meetings_stats) >= 2:
        avg_iterations = np.mean([s['total_iterations'] for s in all_meetings_stats.values()])
        avg_improvement = np.mean([s['improvement'] for s in all_meetings_stats.values()])
        
        if avg_iterations > 30:
            print("   1. ⚙️  調整 early stopping 參數，避免過度疊代")
            print("      • 降低 patience 值 (建議: 3-5)")
            print("      • 提高 min_improvement 閾值 (建議: 0.01)")
        
        if avg_improvement < 0:
            print("   2. 🎯 優化策略選擇機制")
            print("      • 檢查 LLM 改進建議的品質")
            print("      • 調整策略權重和組合邏輯")
        
        max_volatility = max([s['volatility'] for s in all_meetings_stats.values()])
        if max_volatility > 0.1:
            print("   3. 📊 穩定評估指標")
            print("      • 檢查 BERTScore 計算的一致性")
            print("      • 考慮使用多指標平均來減少波動")
    
    print()
    
    # 創建視覺化
    stats_dict = create_trend_visualization()
    
    return stats_dict

if __name__ == "__main__":
    # 確保結果目錄存在
    os.makedirs('results', exist_ok=True)
    
    # 執行分析
    stats = generate_analysis_report()
    
    # 保存統計資料到 JSON
    with open('results/trend_analysis_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("✅ 分析完成！")
    print("📁 結果檔案:")
    print("   • results/quality_trends_analysis.png (視覺化圖表)")
    print("   • results/trend_analysis_stats.json (統計資料)")
