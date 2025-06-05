#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取並分析今天下午三輪會議記錄的內容和品質分數
分析為什麼第二輪內容豐富但分數較低
"""

import re
import json
from datetime import datetime

def extract_meeting_minutes_from_log(log_file_path):
    """從日誌文件提取三輪會議記錄內容和分數"""
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取分數信息
        score_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - MeetingOptimizer - INFO - 第 (\d+) 輪完成，總分: ([-\d.]+)'
        score_matches = re.findall(score_pattern, content)
        
        scores_info = []
        for timestamp_str, round_num, score in score_matches:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            if timestamp.hour >= 13:  # 只取下午的記錄
                scores_info.append({
                    'round': int(round_num),
                    'score': float(score),
                    'timestamp': timestamp_str
                })
        
        print(f"找到 {len(scores_info)} 輪下午的分數記錄:")
        for info in scores_info:
            print(f"  第{info['round']}輪: {info['score']:.4f} ({info['timestamp']})")
        
        # 提取會議記錄內容 - 尋找生成的會議記錄
        meeting_records = []
        
        # 分別查找三輪的會議記錄內容
        for i, score_info in enumerate(scores_info[:3]):  # 只取前三輪
            round_num = score_info['round']
            
            # 在該輪分數時間戳前查找會議記錄內容
            timestamp_pattern = score_info['timestamp'].replace(':', r'\:').replace('-', r'\-').replace(' ', r'\s+')
            
            # 向前查找該輪的會議記錄
            round_pattern = rf'會議名稱：第671次市政會議.*?(?=\d{{4}}-\d{{2}}-\d{{2}}\s+\d{{2}}:\d{{2}}:\d{{2}},\d+\s+-\s+MeetingOptimizer\s+-\s+INFO\s+-\s+第\s+{round_num}\s+輪完成)'
            
            round_match = re.search(round_pattern, content, re.DOTALL)
            if round_match:
                meeting_text = round_match.group(0)
                # 清理和提取實際的會議記錄內容
                clean_text = extract_clean_meeting_content(meeting_text)
                meeting_records.append({
                    'round': round_num,
                    'content': clean_text,
                    'word_count': len(clean_text),
                    'score': score_info['score']
                })
        
        return meeting_records
    
    except Exception as e:
        print(f"錯誤: {e}")
        return []

def extract_clean_meeting_content(raw_text):
    """從原始日誌文本中提取乾淨的會議記錄內容"""
    # 移除日誌格式標記
    lines = raw_text.split('\n')
    clean_lines = []
    
    in_meeting_content = False
    for line in lines:
        # 跳過日誌時間戳行
        if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
            continue
        # 跳過INFO行
        if 'INFO:' in line or '- INFO -' in line:
            continue
        # 跳過空行
        if not line.strip():
            continue
        
        # 檢查是否開始會議內容
        if '會議名稱：' in line or '會議時間：' in line:
            in_meeting_content = True
        
        if in_meeting_content:
            clean_lines.append(line.strip())
    
    return '\n'.join(clean_lines)

def analyze_content_differences(meeting_records):
    """分析三輪會議記錄的內容差異"""
    print("\n" + "="*80)
    print("三輪會議記錄內容與品質分析")
    print("="*80)
    
    for i, record in enumerate(meeting_records):
        print(f"\n📋 第{record['round']}輪會議記錄:")
        print(f"   品質分數: {record['score']:.4f}")
        print(f"   字數統計: {record['word_count']} 字")
        print(f"   內容預覽:")
        
        # 顯示前500字符作為預覽
        preview = record['content'][:500] + "..." if len(record['content']) > 500 else record['content']
        print("   " + "─"*50)
        for line in preview.split('\n')[:10]:  # 只顯示前10行
            if line.strip():
                print(f"   {line}")
        print("   " + "─"*50)
        
        # 分析結構
        content = record['content']
        structure_analysis = {
            '標題數量': len(re.findall(r'^#+\s+', content, re.MULTILINE)),
            '條列項目': len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE)),
            '編號項目': len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE)),
            '段落數': len([p for p in content.split('\n\n') if p.strip()]),
            '包含時間': bool(re.search(r'\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}', content)),
            '包含決議': bool(re.search(r'決議|決定|通過|核定', content)),
            '包含行動項目': bool(re.search(r'行動|執行|負責|期限|完成', content))
        }
        
        print(f"   結構分析: {structure_analysis}")
    
    # 比較分析
    print(f"\n🔍 比較分析:")
    
    # 字數比較
    word_counts = [r['word_count'] for r in meeting_records]
    scores = [r['score'] for r in meeting_records]
    
    print(f"   字數趨勢: {' → '.join(str(w) for w in word_counts)}")
    print(f"   分數趨勢: {' → '.join(f'{s:.4f}' for s in scores)}")
    
    # 找出第二輪的特點
    if len(meeting_records) >= 2:
        second_round = meeting_records[1]
        print(f"\n📉 第二輪分析 (分數: {second_round['score']:.4f}):")
        print(f"   字數: {second_round['word_count']} (最{'多' if second_round['word_count'] == max(word_counts) else '少'})")
        
        # 檢查可能的問題
        content = second_round['content']
        issues = []
        
        # 檢查重複內容
        lines = content.split('\n')
        unique_lines = set(line.strip() for line in lines if line.strip())
        if len(lines) - len(unique_lines) > 5:
            issues.append(f"可能有重複內容 ({len(lines) - len(unique_lines)} 行重複)")
        
        # 檢查結構問題
        if not re.search(r'^#+\s+', content, re.MULTILINE):
            issues.append("缺乏標題結構")
        
        # 檢查內容密度
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        if avg_line_length < 10:
            issues.append(f"行文過短 (平均每行 {avg_line_length:.1f} 字)")
        
        # 檢查專業術語
        if not re.search(r'會議|討論|決議|提案|報告', content):
            issues.append("缺乏會議相關術語")
        
        if issues:
            print(f"   可能問題:")
            for issue in issues:
                print(f"     • {issue}")
        else:
            print(f"   未發現明顯結構問題")
    
    # 提供改善建議
    print(f"\n💡 品質改善分析:")
    if len(meeting_records) >= 3:
        best_round = max(meeting_records, key=lambda x: x['score'])
        worst_round = min(meeting_records, key=lambda x: x['score'])
        
        print(f"   最佳輪次: 第{best_round['round']}輪 ({best_round['score']:.4f})")
        print(f"   最差輪次: 第{worst_round['round']}輪 ({worst_round['score']:.4f})")
        print(f"   分數差距: {best_round['score'] - worst_round['score']:.4f}")
        
        if best_round['round'] == 3:
            print(f"   ✅ 系統顯示學習改進趨勢")
        else:
            print(f"   ⚠️  最佳表現不在最後輪次")

def save_detailed_analysis(meeting_records):
    """保存詳細分析結果"""
    analysis_result = {
        'analysis_time': datetime.now().isoformat(),
        'meeting_rounds': len(meeting_records),
        'rounds_data': []
    }
    
    for record in meeting_records:
        round_data = {
            'round': record['round'],
            'score': record['score'],
            'word_count': record['word_count'],
            'content_preview': record['content'][:200] + "..." if len(record['content']) > 200 else record['content']
        }
        analysis_result['rounds_data'].append(round_data)
    
    with open('/Users/lanss/projects/exam08_提示詞練習重啟/671會議三輪內容分析.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細分析已保存至: 671會議三輪內容分析.json")

def main():
    """主函數"""
    log_file = "/Users/lanss/projects/exam08_提示詞練習重啟/logs/optimization_20250605_141029.log"
    
    print("正在提取今天下午三輪會議記錄內容...")
    
    meeting_records = extract_meeting_minutes_from_log(log_file)
    
    if not meeting_records:
        print("❌ 未能提取到會議記錄內容")
        return
    
    print(f"✅ 成功提取 {len(meeting_records)} 輪會議記錄")
    
    # 分析內容差異
    analyze_content_differences(meeting_records)
    
    # 保存分析結果
    save_detailed_analysis(meeting_records)

if __name__ == "__main__":
    main()
