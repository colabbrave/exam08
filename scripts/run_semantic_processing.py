#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段批次處理腳本
提供簡單的命令行界面來處理會議逐字稿
"""

import argparse
import os
import sys
import json
from pathlib import Path

# 添加scripts目錄到路徑
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from semantic_meeting_processor import SemanticMeetingProcessor


def main():
    parser = argparse.ArgumentParser(description="語意分段會議記錄處理器")
    
    # 基本參數
    parser.add_argument("--input", "-i", required=True, 
                       help="輸入文件路徑或目錄")
    parser.add_argument("--output", "-o", default="output",
                       help="輸出目錄 (默認: output)")
    
    # 模型配置
    parser.add_argument("--splitter-model", default="gemma3:12b",
                       help="語意分段模型 (默認: gemma3:12b)")
    parser.add_argument("--generator-model", 
                       default="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                       help="會議記錄生成模型")
    parser.add_argument("--ollama-url", default="http://localhost:11434/api/generate",
                       help="Ollama API 端點")
    
    # 分段參數
    parser.add_argument("--max-segment-length", type=int, default=4000,
                       help="最大分段長度 (默認: 4000)")
    parser.add_argument("--overlap-length", type=int, default=200,
                       help="段落重疊長度 (默認: 200)")
    
    # 品質控制
    parser.add_argument("--quality-threshold", type=float, default=6.0,
                       help="品質閾值 (默認: 6.0)")
    parser.add_argument("--disable-quality-check", action="store_true",
                       help="禁用品質檢查")
    
    # 批次處理
    parser.add_argument("--batch", action="store_true",
                       help="批次處理模式（輸入為目錄）")
    parser.add_argument("--file-pattern", default="*.txt",
                       help="批次處理時的文件匹配模式 (默認: *.txt)")
    
    # 其他選項
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="詳細輸出")
    
    args = parser.parse_args()
    
    # 設置日誌級別
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    # 初始化處理器
    processor = SemanticMeetingProcessor(
        splitter_model=args.splitter_model,
        generator_model=args.generator_model,
        ollama_url=args.ollama_url,
        max_segment_length=args.max_segment_length,
        overlap_length=args.overlap_length,
        quality_threshold=args.quality_threshold
    )
    
    try:
        if args.batch:
            # 批次處理模式
            if not os.path.isdir(args.input):
                print(f"錯誤: 批次模式需要輸入目錄，但 {args.input} 不是目錄")
                sys.exit(1)
            
            print(f"開始批次處理目錄: {args.input}")
            print(f"文件匹配模式: {args.file_pattern}")
            
            results = processor.batch_process_files(
                input_dir=args.input,
                output_dir=args.output,
                file_pattern=args.file_pattern
            )
            
            # 統計結果
            total = len(results)
            successful = len([r for r in results if r.get("status") == "success"])
            failed = total - successful
            
            print(f"\n=== 批次處理完成 ===")
            print(f"總文件數: {total}")
            print(f"成功: {successful}")
            print(f"失敗: {failed}")
            
            if failed > 0:
                print("\n失敗的文件:")
                for result in results:
                    if result.get("status") == "error":
                        print(f"  - {result['source_file']}: {result.get('error', '未知錯誤')}")
            
        else:
            # 單文件處理模式
            if not os.path.isfile(args.input):
                print(f"錯誤: 輸入文件 {args.input} 不存在")
                sys.exit(1)
            
            print(f"開始處理文件: {args.input}")
            
            # 讀取文件
            with open(args.input, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 處理文件
            result = processor.process_transcript(
                content,
                output_dir=args.output,
                enable_quality_check=not args.disable_quality_check
            )
            
            # 顯示結果
            print(f"\n=== 處理完成 ===")
            print(f"狀態: {result['status']}")
            
            if result['status'] == 'success':
                print(f"原文長度: {result['original_length']} 字元")
                print(f"分段數量: {result.get('segment_count', 0)}")
                
                if not args.disable_quality_check:
                    print(f"品質分數: {result.get('quality_score', '未評估'):.2f}/10")
                    print(f"品質可接受: {'是' if result.get('quality_acceptable') else '否'}")
                
                print(f"處理時間: {result.get('processing_time', 0):.2f} 秒")
                print(f"輸出目錄: {result['process_dir']}")
                
                if result.get('final_record_file'):
                    print(f"最終會議記錄: {result['final_record_file']}")
                    
                    # 預覽會議記錄開頭
                    try:
                        with open(result['final_record_file'], 'r', encoding='utf-8') as f:
                            preview = f.read(500)
                        print(f"\n會議記錄預覽:")
                        print("-" * 50)
                        print(preview + "..." if len(preview) == 500 else preview)
                        print("-" * 50)
                    except:
                        pass
                
            else:
                print(f"錯誤: {result.get('error', '未知錯誤')}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n處理被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
