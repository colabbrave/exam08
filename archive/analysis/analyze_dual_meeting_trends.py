#!/usr/bin/env python3
"""
分析今天下午兩個會議的三輪優化品質分數趨勢
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_dual_meeting_comparison():
    """創建兩個會議的三輪優化對比圖"""
    
    # 數據
    rounds = ['第一輪', '第二輪', '第三輪']
    meeting_671_scores = [0.6628, 0.6530, 0.7326]
    meeting_672_scores = [0.7369, 0.6902, 0.7057]
    
    # 創建圖表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # === 左圖：雙線趨勢對比 ===
    x = np.arange(len(rounds))
    
    # 繪製線條
    line1 = ax1.plot(x, meeting_671_scores, 'o-', linewidth=3, markersize=8, 
                     color='#2E86C1', label='第671次會議(5月13日)')
    line2 = ax1.plot(x, meeting_672_scores, 's-', linewidth=3, markersize=8, 
                     color='#E74C3C', label='第672次會議(5月20日)')
    
    # 標註數值
    for i, (score1, score2) in enumerate(zip(meeting_671_scores, meeting_672_scores)):
        ax1.annotate(f'{score1:.4f}', (i, score1), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=10, color='#2E86C1', fontweight='bold')
        ax1.annotate(f'{score2:.4f}', (i, score2), textcoords="offset points", 
                    xytext=(0,-15), ha='center', fontsize=10, color='#E74C3C', fontweight='bold')
    
    ax1.set_xlabel('優化輪次', fontsize=12, fontweight='bold')
    ax1.set_ylabel('品質分數', fontsize=12, fontweight='bold')
    ax1.set_title('今天下午兩會議三輪優化品質分數對比\n(2025年6月5日下午執行)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(rounds)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_ylim(0.6, 0.8)
    
    # === 右圖：柱狀圖對比 ===
    width = 0.35
    x_bar = np.arange(len(rounds))
    
    bars1 = ax2.bar(x_bar - width/2, meeting_671_scores, width, 
                    label='第671次會議', color='#2E86C1', alpha=0.8)
    bars2 = ax2.bar(x_bar + width/2, meeting_672_scores, width, 
                    label='第672次會議', color='#E74C3C', alpha=0.8)
    
    # 標註數值
    for bar in bars1:
        height = bar.get_height()
        ax2.annotate(f'{height:.4f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',
                    fontsize=10, fontweight='bold')
    
    for bar in bars2:
        height = bar.get_height()
        ax2.annotate(f'{height:.4f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',
                    fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('優化輪次', fontsize=12, fontweight='bold')
    ax2.set_ylabel('品質分數', fontsize=12, fontweight='bold')
    ax2.set_title('三輪優化分數柱狀圖對比', fontsize=14, fontweight='bold', pad=20)
    ax2.set_xticks(x_bar)
    ax2.set_xticklabels(rounds)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend(fontsize=11)
    ax2.set_ylim(0.6, 0.8)
    
    plt.tight_layout()
    plt.savefig('今天下午_兩會議三輪優化對比.png', dpi=300, bbox_inches='tight')
    plt.close()  # 不顯示圖表，只保存
    
    # 創建詳細分析表格
    analysis_data = {
        '會議': ['第671次會議', '第672次會議'],
        '第一輪': [0.6628, 0.7369],
        '第二輪': [0.6530, 0.6902],
        '第三輪': [0.7326, 0.7057],
        '最佳輪次': ['第三輪', '第一輪'],
        '最佳分數': [0.7326, 0.7369],
        '最差輪次': ['第二輪', '第二輪'],
        '最差分數': [0.6530, 0.6902],
        '總改善幅度': ['+10.5%', '-4.2%'],
        '第三輪改善': ['+12.2%', '+2.2%']
    }
    
    df = pd.DataFrame(analysis_data)
    print("=== 今天下午兩會議三輪優化詳細分析 ===")
    print(df.to_string(index=False))
    
    # 保存CSV
    df.to_csv('今天下午_兩會議三輪優化分析.csv', index=False, encoding='utf-8-sig')
    
    return df

def analyze_improvement_patterns():
    """分析改善模式"""
    print("\n=== 改善模式分析 ===")
    
    # 第671次會議分析
    print("📊 第671次會議(5月13日):")
    print("  • 第一→第二輪: 0.6628 → 0.6530 (下降1.5%)")
    print("  • 第二→第三輪: 0.6530 → 0.7326 (提升12.2%)")
    print("  • 整體改善: +10.5%")
    print("  • 特點: 低開高走，第三輪強力突破")
    
    print("\n📊 第672次會議(5月20日):")
    print("  • 第一→第二輪: 0.7369 → 0.6902 (下降6.3%)")
    print("  • 第二→第三輪: 0.6902 → 0.7057 (提升2.2%)")
    print("  • 整體變化: -4.2%")
    print("  • 特點: 高開低走，恢復有限")
    
    print("\n🔍 共同現象:")
    print("  • 兩個會議都在第二輪出現分數下降")
    print("  • 第671次展現更強的學習和改善能力")
    print("  • 第672次第一輪表現優異但後續穩定性不足")

if __name__ == "__main__":
    print("開始分析今天下午兩會議三輪優化記錄...")
    df = create_dual_meeting_comparison()
    analyze_improvement_patterns()
    print("\n✅ 分析完成，圖表已保存為 '今天下午_兩會議三輪優化對比.png'")
    print("📄 詳細數據已保存為 '今天下午_兩會議三輪優化分析.csv'")
