#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今天下午(2025-06-05)品質分數趨勢分析

專注分析今天下午運行的優化流程品質分數變化
"""

import re
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np

def extract_afternoon_scores(log_file_path):
    """從今天下午的日誌文件提取品質分數"""
    scores = []
    rounds = []
    timestamps = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取輪次和總分，包含時間戳
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - MeetingOptimizer - INFO - 第 (\d+) 輪完成，總分: ([-\d.]+)'
        matches = re.findall(pattern, content)
        
        print(f"找到 {len(matches)} 條分數記錄")
        
        for timestamp_str, round_num, score in matches:
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                # 只取今天下午（13點後）的記錄
                if timestamp.hour >= 13:
                    rounds.append(int(round_num))
                    scores.append(float(score))
                    timestamps.append(timestamp)
                    print(f"  第{round_num}輪: {score} (時間: {timestamp_str})")
            except ValueError as e:
                print(f"解析時間或分數失敗: {e}")
                continue
        
        return rounds, scores, timestamps
    
    except Exception as e:
        print(f"錯誤: 無法讀取日誌文件 {log_file_path}: {e}")
        return [], [], []

def analyze_afternoon_trends(rounds, scores, timestamps):
    """分析今天下午的品質分數趨勢"""
    if not rounds or not scores:
        return None, None
    
    df = pd.DataFrame({
        'Round': rounds,
        'Score': scores,
        'Timestamp': timestamps,
        'Time_Str': [ts.strftime('%H:%M:%S') for ts in timestamps]
    })
    
    # 按時間排序
    df = df.sort_values('Timestamp').reset_index(drop=True)
    
    # 計算統計指標
    analysis = {
        '最高分數': max(scores),
        '最低分數': min(scores),
        '平均分數': np.mean(scores),
        '標準差': np.std(scores),
        '最佳輪次': rounds[scores.index(max(scores))],
        '最差輪次': rounds[scores.index(min(scores))],
        '總輪次': len(rounds),
        '開始時間': df.iloc[0]['Time_Str'],
        '結束時間': df.iloc[-1]['Time_Str'],
        '總耗時': str(df.iloc[-1]['Timestamp'] - df.iloc[0]['Timestamp'])
    }
    
    # 檢測是否有多個優化序列
    sequences = []
    current_seq = []
    
    for i, row in df.iterrows():
        if i == 0 or row['Round'] > df.iloc[i-1]['Round']:
            current_seq.append(i)
        else:
            # 開始新序列
            if current_seq:
                sequences.append(current_seq)
            current_seq = [i]
    
    if current_seq:
        sequences.append(current_seq)
    
    analysis['優化序列數'] = len(sequences)
    
    return df, analysis, sequences

def create_afternoon_visualization(df, analysis, sequences, save_path=None):
    """創建今天下午品質分數趨勢可視化圖表"""
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 圖1: 按時間序列的分數趨勢
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, seq_indices in enumerate(sequences):
        seq_df = df.iloc[seq_indices]
        color = colors[i % len(colors)]
        label = f'優化序列 {i+1}'
        
        ax1.plot(range(len(seq_df)), seq_df['Score'], 'o-', 
                color=color, linewidth=2, markersize=8, label=label)
        
        # 標記最高分和最低分
        if len(seq_df) > 1:
            max_idx = seq_df['Score'].idxmax()
            min_idx = seq_df['Score'].idxmin()
            
            max_pos = seq_indices.index(max_idx)
            min_pos = seq_indices.index(min_idx)
            
            ax1.scatter(max_pos, seq_df.loc[max_idx, 'Score'], 
                       color='green', s=100, marker='^', alpha=0.8)
            ax1.scatter(min_pos, seq_df.loc[min_idx, 'Score'], 
                       color='red', s=100, marker='v', alpha=0.8)
    
    ax1.set_xlabel('序列內輪次')
    ax1.set_ylabel('品質分數')
    ax1.set_title(f'今天下午品質分數趨勢 ({analysis["開始時間"]} - {analysis["結束時間"]})', 
                 fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 圖2: 時間軸分析
    ax2.plot(df.index, df['Score'], 'bo-', linewidth=2, markersize=6)
    
    # 標記不同優化序列的邊界
    for i, seq_indices in enumerate(sequences[:-1]):
        boundary = seq_indices[-1] + 0.5
        ax2.axvline(x=boundary, color='red', linestyle='--', alpha=0.6)
    
    # 添加時間標籤
    time_labels = [df.iloc[i]['Time_Str'] if i % max(1, len(df)//8) == 0 
                  else '' for i in range(len(df))]
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(time_labels, rotation=45)
    
    ax2.set_xlabel('時間')
    ax2.set_ylabel('品質分數')
    ax2.set_title('按時間順序的分數變化', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # 標記整體最高和最低分
    overall_max_idx = df['Score'].idxmax()
    overall_min_idx = df['Score'].idxmin()
    
    ax2.scatter(overall_max_idx, df.loc[overall_max_idx, 'Score'], 
               color='green', s=100, marker='^', 
               label=f'最高分: {analysis["最高分數"]:.4f}')
    ax2.scatter(overall_min_idx, df.loc[overall_min_idx, 'Score'], 
               color='red', s=100, marker='v',
               label=f'最低分: {analysis["最低分數"]:.4f}')
    
    ax2.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"圖表已保存至: {save_path}")
    
    plt.show()

def generate_afternoon_report(df, analysis, sequences):
    """生成今天下午的詳細分析報告"""
    print("=" * 80)
    print("今天下午(2025-06-05)品質分數趨勢分析報告")
    print("=" * 80)
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("⏰ 時間範圍:")
    print(f"   開始時間: {analysis['開始時間']}")
    print(f"   結束時間: {analysis['結束時間']}")
    print(f"   總耗時: {analysis['總耗時']}")
    print()
    
    print("📊 整體統計:")
    print(f"   優化序列數: {analysis['優化序列數']} 個")
    print(f"   總輪次: {analysis['總輪次']} 輪")
    print(f"   最高品質分數: {analysis['最高分數']:.4f}")
    print(f"   最低品質分數: {analysis['最低分數']:.4f}")
    print(f"   平均品質分數: {analysis['平均分數']:.4f}")
    print(f"   分數標準差: {analysis['標準差']:.4f}")
    print()
    
    print("🔍 各優化序列詳細分析:")
    for i, seq_indices in enumerate(sequences):
        seq_df = df.iloc[seq_indices]
        print(f"\n   序列 {i+1} ({len(seq_df)} 輪):")
        print(f"   時間範圍: {seq_df.iloc[0]['Time_Str']} - {seq_df.iloc[-1]['Time_Str']}")
        
        if len(seq_df) > 1:
            initial_score = seq_df.iloc[0]['Score']
            final_score = seq_df.iloc[-1]['Score']
            improvement = final_score - initial_score
            improvement_pct = (improvement / abs(initial_score)) * 100 if initial_score != 0 else 0
            
            print(f"   初始分數: {initial_score:.4f}")
            print(f"   最終分數: {final_score:.4f}")
            print(f"   改善幅度: {improvement:+.4f} ({improvement_pct:+.1f}%)")
            print(f"   序列最高: {seq_df['Score'].max():.4f}")
            print(f"   序列最低: {seq_df['Score'].min():.4f}")
            
            # 趨勢分析
            if improvement > 0.01:
                trend = "📈 明顯改善"
            elif improvement < -0.01:
                trend = "📉 明顯下降"
            else:
                trend = "➡️ 基本持平"
            print(f"   趨勢評估: {trend}")
        else:
            print(f"   分數: {seq_df.iloc[0]['Score']:.4f}")
    
    print("\n" + "=" * 50)
    print("🎯 關鍵發現:")
    
    # 最佳序列識別
    if len(sequences) > 1:
        seq_averages = []
        for seq_indices in sequences:
            seq_df = df.iloc[seq_indices]
            seq_averages.append(seq_df['Score'].mean())
        
        best_seq_idx = seq_averages.index(max(seq_averages))
        print(f"   • 最佳優化序列: 序列 {best_seq_idx + 1} (平均分數: {max(seq_averages):.4f})")
    
    # 時間效率分析
    total_minutes = (df.iloc[-1]['Timestamp'] - df.iloc[0]['Timestamp']).total_seconds() / 60
    rounds_per_hour = analysis['總輪次'] / (total_minutes / 60)
    print(f"   • 處理效率: {rounds_per_hour:.1f} 輪/小時")
    
    # 穩定性分析
    volatility = analysis['標準差'] / abs(analysis['平均分數']) if analysis['平均分數'] != 0 else 0
    stability = "高" if volatility < 0.1 else "中" if volatility < 0.2 else "低"
    print(f"   • 分數穩定性: {stability} (變異係數: {volatility:.2%})")
    
    # 連續性分析
    consecutive_improvements = 0
    max_consecutive_improvements = 0
    consecutive_declines = 0
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
    
    print("\n📋 今日總結:")
    overall_improvement = df.iloc[-1]['Score'] - df.iloc[0]['Score']
    if overall_improvement > 0.05:
        print("   ✅ 今天下午的優化效果顯著，系統表現良好")
    elif overall_improvement > 0:
        print("   ✅ 今天下午有輕微改善，整體趨勢良好")
    else:
        print("   ⚠️  今天下午分數未見明顯改善，建議檢視策略")
    
    if analysis['最高分數'] > 0.7:
        print("   🎯 已達到高品質水準 (>0.7)，可作為優質模板")
    elif analysis['最高分數'] > 0.6:
        print("   📊 達到中等品質水準 (>0.6)，仍有改善空間")
    else:
        print("   📈 品質水準待提升，建議調整策略組合")
    
    print("=" * 80)

def main():
    """主函數"""
    log_file = "/Users/lanss/projects/exam08_提示詞練習重啟/logs/optimization_20250605_141029.log"
    
    print("正在分析今天下午的品質分數趨勢...")
    
    # 提取分數數據
    rounds, scores, timestamps = extract_afternoon_scores(log_file)
    
    if not rounds:
        print("❌ 未找到今天下午的品質分數數據")
        return
    
    print(f"✅ 成功提取今天下午 {len(rounds)} 輪的品質分數數據")
    
    # 分析趨勢
    df, analysis, sequences = analyze_afternoon_trends(rounds, scores, timestamps)
    
    if df is None:
        print("❌ 數據分析失敗")
        return
    
    # 生成報告
    generate_afternoon_report(df, analysis, sequences)
    
    # 創建可視化圖表
    save_path = "/Users/lanss/projects/exam08_提示詞練習重啟/今天下午_品質分數趨勢.png"
    create_afternoon_visualization(df, analysis, sequences, save_path)
    
    # 保存數據到CSV
    csv_path = "/Users/lanss/projects/exam08_提示詞練習重啟/今天下午_品質分數數據.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"數據已保存至: {csv_path}")

if __name__ == "__main__":
    main()
