#!/usr/bin/env python3
"""
測試修正後的 _simple_segment 方法
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 測試文本 - 創建一個會導致203段問題的文本
test_text = "這是一個測試文本。" * 3000  # 大約15000字元

print(f"測試文本長度: {len(test_text)} 字元")

# 導入修正後的 MeetingOptimizer
from scripts.optimize_meeting_minutes import MeetingOptimizer, OptimizationConfig

# 創建優化器實例
config = OptimizationConfig(
    max_segment_length=4000,
    segment_overlap=200,
    enable_semantic_segmentation=False  # 直接測試簡單分段
)

optimizer = MeetingOptimizer(config)

# 測試簡單分段方法
print("開始測試 _simple_segment 方法...")
segments = optimizer._simple_segment(test_text, 4000)

print(f"分段結果: {len(segments)} 個分段")
print("\n各分段長度:")
for i, segment in enumerate(segments):
    print(f"  第 {i+1} 段: {len(segment['content'])} 字元")

# 驗證沒有過短的分段
short_segments = [s for s in segments if len(s['content']) < 100]
if short_segments:
    print(f"\n警告: 發現 {len(short_segments)} 個過短分段!")
    for i, s in enumerate(short_segments):
        print(f"  過短分段 {i+1}: {len(s['content'])} 字元")
else:
    print("\n✓ 沒有發現過短分段，修正成功!")

# 驗證分段內容完整性
total_chars = sum(len(s['content']) for s in segments)
print(f"\n分段內容總字元數: {total_chars}")
print(f"原始文本字元數: {len(test_text)}")
print(f"字元遺失: {len(test_text) - total_chars}")
