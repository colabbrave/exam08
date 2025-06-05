#!/usr/bin/env python3
"""
分析今天下午兩個會議的三輪優化品質分數趨勢 - 純數據版本
"""
import pandas as pd

def analyze_dual_meeting_trends():
    """分析兩個會議的三輪優化趨勢"""
    
    # 數據
    meeting_671_scores = [0.6628, 0.6530, 0.7326]
    meeting_672_scores = [0.7369, 0.6902, 0.7057]
    rounds = ['第一輪', '第二輪', '第三輪']
    
    print("=== 今天下午兩會議三輪優化執行記錄分析 ===")
    print("執行日期: 2025年6月5日下午")
    print("執行時間: 14:10:29 - 15:52:40 (約1小時42分鐘)")
    print()
    
    # 詳細分數表格
    print("📊 詳細分數記錄:")
    print("-" * 60)
    print(f"{'輪次':<10} {'第671次會議':<15} {'第672次會議':<15} {'差距':<10}")
    print("-" * 60)
    
    for i, round_name in enumerate(rounds):
        score_671 = meeting_671_scores[i]
        score_672 = meeting_672_scores[i]
        diff = score_672 - score_671
        print(f"{round_name:<10} {score_671:<15.4f} {score_672:<15.4f} {diff:+.4f}")
    
    print("-" * 60)
    
    # 變化分析
    print("\n📈 變化趨勢分析:")
    print("\n🔵 第671次會議(5月13日):")
    change_671_1to2 = (meeting_671_scores[1] - meeting_671_scores[0]) / meeting_671_scores[0] * 100
    change_671_2to3 = (meeting_671_scores[2] - meeting_671_scores[1]) / meeting_671_scores[1] * 100
    total_change_671 = (meeting_671_scores[2] - meeting_671_scores[0]) / meeting_671_scores[0] * 100
    
    print(f"  • 第一→第二輪: {meeting_671_scores[0]:.4f} → {meeting_671_scores[1]:.4f} ({change_671_1to2:+.1f}%)")
    print(f"  • 第二→第三輪: {meeting_671_scores[1]:.4f} → {meeting_671_scores[2]:.4f} ({change_671_2to3:+.1f}%)")
    print(f"  • 整體變化: {meeting_671_scores[0]:.4f} → {meeting_671_scores[2]:.4f} ({total_change_671:+.1f}%)")
    
    print("\n🔴 第672次會議(5月20日):")
    change_672_1to2 = (meeting_672_scores[1] - meeting_672_scores[0]) / meeting_672_scores[0] * 100
    change_672_2to3 = (meeting_672_scores[2] - meeting_672_scores[1]) / meeting_672_scores[1] * 100
    total_change_672 = (meeting_672_scores[2] - meeting_672_scores[0]) / meeting_672_scores[0] * 100
    
    print(f"  • 第一→第二輪: {meeting_672_scores[0]:.4f} → {meeting_672_scores[1]:.4f} ({change_672_1to2:+.1f}%)")
    print(f"  • 第二→第三輪: {meeting_672_scores[1]:.4f} → {meeting_672_scores[2]:.4f} ({change_672_2to3:+.1f}%)")
    print(f"  • 整體變化: {meeting_672_scores[0]:.4f} → {meeting_672_scores[2]:.4f} ({total_change_672:+.1f}%)")
    
    # 統計摘要
    print("\n📋 統計摘要:")
    print("-" * 50)
    stats_data = {
        '指標': ['最高分', '最低分', '平均分', '標準差', '最佳輪次', '最差輪次'],
        '第671次會議': [
            f"{max(meeting_671_scores):.4f}",
            f"{min(meeting_671_scores):.4f}",
            f"{sum(meeting_671_scores)/len(meeting_671_scores):.4f}",
            f"{pd.Series(meeting_671_scores).std():.4f}",
            f"第{meeting_671_scores.index(max(meeting_671_scores))+1}輪",
            f"第{meeting_671_scores.index(min(meeting_671_scores))+1}輪"
        ],
        '第672次會議': [
            f"{max(meeting_672_scores):.4f}",
            f"{min(meeting_672_scores):.4f}",
            f"{sum(meeting_672_scores)/len(meeting_672_scores):.4f}",
            f"{pd.Series(meeting_672_scores).std():.4f}",
            f"第{meeting_672_scores.index(max(meeting_672_scores))+1}輪",
            f"第{meeting_672_scores.index(min(meeting_672_scores))+1}輪"
        ]
    }
    
    for i, metric in enumerate(stats_data['指標']):
        print(f"{metric:<10} {stats_data['第671次會議'][i]:<15} {stats_data['第672次會議'][i]:<15}")
    
    print("-" * 50)
    
    # 關鍵發現
    print("\n🔍 關鍵發現:")
    print("1. 【第二輪瓶頸現象】兩個會議都在第二輪出現分數下降:")
    print(f"   - 第671次: 下降{abs(change_671_1to2):.1f}%")
    print(f"   - 第672次: 下降{abs(change_672_1to2):.1f}%")
    
    print("\n2. 【恢復能力差異】第三輪的恢復表現截然不同:")
    print(f"   - 第671次: 強力反彈 +{change_671_2to3:.1f}% (0.0796分)")
    print(f"   - 第672次: 溫和恢復 +{change_672_2to3:.1f}% (0.0155分)")
    
    print("\n3. 【整體表現】:")
    print(f"   - 第671次: 低開高走，整體改善{total_change_671:+.1f}%")
    print(f"   - 第672次: 高開後回落，整體下降{abs(total_change_672):.1f}%")
    
    print("\n4. 【最佳分數】:")
    if max(meeting_671_scores) > max(meeting_672_scores):
        print(f"   - 第671次第三輪創下最高分: {max(meeting_671_scores):.4f}")
    else:
        print(f"   - 第672次第一輪創下最高分: {max(meeting_672_scores):.4f}")
    
    # 保存詳細數據
    detailed_data = {
        '會議': ['第671次會議', '第671次會議', '第671次會議', 
                 '第672次會議', '第672次會議', '第672次會議'],
        '輪次': ['第一輪', '第二輪', '第三輪', '第一輪', '第二輪', '第三輪'],
        '品質分數': meeting_671_scores + meeting_672_scores,
        '執行時間': ['14:10-14:26', '14:26-14:46', '14:46-15:05',
                   '15:05-15:18', '15:18-15:36', '15:36-15:52']
    }
    
    df = pd.DataFrame(detailed_data)
    df.to_csv('今天下午_兩會議三輪優化詳細記錄.csv', index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 分析完成！")
    print("📄 詳細記錄已保存為: '今天下午_兩會議三輪優化詳細記錄.csv'")
    
    return df

if __name__ == "__main__":
    analyze_dual_meeting_trends()
