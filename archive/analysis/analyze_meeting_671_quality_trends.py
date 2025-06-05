#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第671次市政會議114年5月13日品質分數趨勢分析

從日誌中提取品質分數趨勢並生成可視化圖表
"""

import re
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np

def extract_quality_scores(log_file_path):
    """從日誌文件提取品質分數"""
    scores = []
    rounds = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正則表達式提取輪次和總分，避免重複
        pattern = r'\[.*?\] \[INFO\] 第 (\d+) 輪完成，總分: ([-\d.]+)'
        matches = re.findall(pattern, content)
        
        # 去重處理，每個輪次只保留一次記錄
        seen_rounds = set()
        for round_num, score in matches:
            round_int = int(round_num)
            if round_int not in seen_rounds:
                rounds.append(round_int)
                scores.append(float(score))
                seen_rounds.add(round_int)
        
        return rounds, scores
    
    except Exception as e:
        print(f"錯誤: 無法讀取日誌文件 {log_file_path}: {e}")
        return [], []

def analyze_trends(rounds, scores):
    """分析品質分數趨勢"""
    if not rounds or not scores:
        return None
    
    df = pd.DataFrame({
        'Round': rounds,
        'Score': scores
    })
    
    # 計算統計指標
    analysis = {
        '最高分數': max(scores),
        '最低分數': min(scores),
        '平均分數': np.mean(scores),
        '標準差': np.std(scores),
        '最佳輪次': rounds[scores.index(max(scores))],
        '最差輪次': rounds[scores.index(min(scores))],
        '改善趨勢': 'Y' if scores[-1] > scores[0] else 'N',
        '總輪次': len(rounds)
    }
    
    # 計算移動平均
    if len(scores) >= 3:
        df['Moving_Avg'] = df['Score'].rolling(window=3, center=True).mean()
    
    return df, analysis

def create_trend_visualization(df, analysis, save_path=None):
    """創建品質分數趨勢可視化圖表"""
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']  # 支援中文
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 圖1: 品質分數趨勢線
    ax1.plot(df['Round'], df['Score'], 'bo-', linewidth=2, markersize=8, label='實際分數')
    
    # 添加移動平均線（如果有的話）
    if 'Moving_Avg' in df.columns:
        ax1.plot(df['Round'], df['Moving_Avg'], 'r--', linewidth=2, alpha=0.7, label='3輪移動平均')
    
    # 標記最高分和最低分
    max_idx = df['Score'].idxmax()
    min_idx = df['Score'].idxmin()
    
    ax1.scatter(df.loc[max_idx, 'Round'], df.loc[max_idx, 'Score'], 
               color='green', s=100, marker='^', label=f'最高分 ({analysis["最高分數"]:.4f})')
    ax1.scatter(df.loc[min_idx, 'Round'], df.loc[min_idx, 'Score'], 
               color='red', s=100, marker='v', label=f'最低分 ({analysis["最低分數"]:.4f})')
    
    ax1.set_xlabel('優化輪次')
    ax1.set_ylabel('品質分數')
    ax1.set_title('第671次市政會議114年5月13日 - 品質分數優化趨勢', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 設置x軸刻度
    ax1.set_xticks(df['Round'])
    
    # 圖2: 分數分佈直方圖
    ax2.hist(df['Score'], bins=min(10, len(df)), alpha=0.7, color='skyblue', edgecolor='black')
    ax2.axvline(analysis['平均分數'], color='red', linestyle='--', linewidth=2, label=f'平均分數: {analysis["平均分數"]:.4f}')
    ax2.set_xlabel('品質分數')
    ax2.set_ylabel('頻次')
    ax2.set_title('品質分數分佈', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"圖表已保存至: {save_path}")
    
    plt.show()

def generate_report(df, analysis):
    """生成詳細的分析報告"""
    print("=" * 80)
    print("第671次市政會議114年5月13日 - 品質分數趨勢分析報告")
    print("=" * 80)
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("📊 基本統計:")
    print(f"   總優化輪次: {analysis['總輪次']} 輪")
    print(f"   最高品質分數: {analysis['最高分數']:.4f} (第{analysis['最佳輪次']}輪)")
    print(f"   最低品質分數: {analysis['最低分數']:.4f} (第{analysis['最差輪次']}輪)")
    print(f"   平均品質分數: {analysis['平均分數']:.4f}")
    print(f"   分數標準差: {analysis['標準差']:.4f}")
    print()
    
    print("📈 趨勢分析:")
    initial_score = df.iloc[0]['Score']
    final_score = df.iloc[-1]['Score']
    improvement = final_score - initial_score
    improvement_pct = (improvement / abs(initial_score)) * 100 if initial_score != 0 else 0
    
    print(f"   初始分數: {initial_score:.4f}")
    print(f"   最終分數: {final_score:.4f}")
    print(f"   總改善幅度: {improvement:+.4f} ({improvement_pct:+.1f}%)")
    print(f"   整體趨勢: {'改善' if improvement > 0 else '下降' if improvement < 0 else '持平'}")
    print()
    
    print("🔍 詳細輪次分析:")
    print("   輪次  |  分數    |  變化    |  相對變化%")
    print("   -----|----------|----------|----------")
    
    for i, row in df.iterrows():
        round_num = int(row['Round'])
        score = row['Score']
        
        if i == 0:
            change = 0
            change_pct = 0
        else:
            prev_score = df.iloc[i-1]['Score']
            change = score - prev_score
            change_pct = (change / abs(prev_score)) * 100 if prev_score != 0 else 0
        
        change_str = f"{change:+.4f}" if change != 0 else "  --  "
        change_pct_str = f"{change_pct:+.1f}%" if change != 0 else "  -- "
        
        print(f"   {round_num:4d}  | {score:8.4f} | {change_str:8s} | {change_pct_str:8s}")
    
    print()
    print("💡 關鍵發現:")
    
    # 尋找連續改善或下降的區間
    consecutive_improvements = 0
    consecutive_declines = 0
    max_consecutive_improvements = 0
    max_consecutive_declines = 0
    
    for i in range(1, len(df)):
        current_score = df.iloc[i]['Score']
        prev_score = df.iloc[i-1]['Score']
        
        if current_score > prev_score:
            consecutive_improvements += 1
            consecutive_declines = 0
            max_consecutive_improvements = max(max_consecutive_improvements, consecutive_improvements)
        elif current_score < prev_score:
            consecutive_declines += 1
            consecutive_improvements = 0
            max_consecutive_declines = max(max_consecutive_declines, consecutive_declines)
        else:
            consecutive_improvements = 0
            consecutive_declines = 0
    
    print(f"   • 最長連續改善: {max_consecutive_improvements} 輪")
    print(f"   • 最長連續下降: {max_consecutive_declines} 輪")
    
    # 波動性分析
    volatility = analysis['標準差'] / abs(analysis['平均分數']) if analysis['平均分數'] != 0 else 0
    print(f"   • 分數波動性: {volatility:.2%} ({'高' if volatility > 0.5 else '中' if volatility > 0.2 else '低'})")
    
    # 最佳策略識別
    best_round = analysis['最佳輪次']
    print(f"   • 最佳表現在第{best_round}輪，建議重點分析該輪的策略組合")
    print()
    
    print("📋 建議:")
    if improvement > 0:
        print("   ✅ 系統成功實現品質改善，優化策略有效")
    else:
        print("   ⚠️  整體分數未見改善，建議檢討優化策略")
    
    if volatility > 0.3:
        print("   ⚠️  分數波動較大，建議增加策略穩定性")
    
    if analysis['最高分數'] > 0.5:
        print("   ✅ 已達到較高品質水準，可作為基準模板")
    else:
        print("   💡 尚未達到理想品質水準，建議繼續優化")
    
    print("=" * 80)

def main():
    """主函數"""
    log_file = "/Users/lanss/projects/exam08_提示詞練習重啟/logs/optimization_20250603_094250.log"
    
    print("正在分析第671次市政會議114年5月13日的品質分數趨勢...")
    
    # 提取分數數據
    rounds, scores = extract_quality_scores(log_file)
    
    if not rounds:
        print("❌ 未找到品質分數數據")
        return
    
    print(f"✅ 成功提取 {len(rounds)} 輪的品質分數數據")
    
    # 分析趨勢
    df, analysis = analyze_trends(rounds, scores)
    
    if df is None:
        print("❌ 數據分析失敗")
        return
    
    # 生成報告
    generate_report(df, analysis)
    
    # 創建可視化圖表
    save_path = "/Users/lanss/projects/exam08_提示詞練習重啟/第671次市政會議_品質分數趨勢.png"
    create_trend_visualization(df, analysis, save_path)
    
    # 保存數據到CSV
    csv_path = "/Users/lanss/projects/exam08_提示詞練習重啟/第671次市政會議_品質分數數據.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"數據已保存至: {csv_path}")

if __name__ == "__main__":
    main()
