#!/usr/bin/env python3
"""
測試邊界情況的分段
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.optimize_meeting_minutes import MeetingOptimizer, OptimizationConfig

# 測試不同長度的文本
test_cases = [
    ("短文本", "這是短文本。" * 50),  # ~500字元
    ("正好4000字元", "這是測試文本。" * 571),  # 約4000字元
    ("4100字元", "這是測試文本。" * 586),  # 約4100字元
    ("邊界情況", "這是測試文本。" * 600 + "最後一段很短"),  # 約4200字元，最後很短
    ("實際會議記錄長度", "這是實際會議記錄測試。" * 950),  # 約14000字元，類似實際情況
]

config = OptimizationConfig(
    max_segment_length=4000,
    segment_overlap=200,
    enable_semantic_segmentation=False
)

optimizer = MeetingOptimizer(config)

for name, text in test_cases:
    print(f"\n=== 測試 {name} (長度: {len(text)} 字元) ===")
    segments = optimizer._simple_segment(text, 4000)
    
    print(f"分段數量: {len(segments)}")
    for i, segment in enumerate(segments):
        print(f"  第 {i+1} 段: {len(segment['content'])} 字元")
    
    # 檢查過短分段
    short_segments = [s for s in segments if len(s['content']) < 50]
    if short_segments:
        print(f"⚠️  發現 {len(short_segments)} 個過短分段!")
    else:
        print("✓ 分段長度正常")
