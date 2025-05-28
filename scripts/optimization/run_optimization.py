#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
會議記錄模板優化腳本

這個腳本實現了完整的會議記錄模板優化流程，包括：
1. 加載參考會議記錄
2. 初始化穩定性優化器
3. 執行優化循環
4. 保存優化結果
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent.absolute()))

from scripts.optimization.stability_optimizer import StabilityOptimizer, optimize_meeting_minutes


def load_text_files(directory: Path, file_type: str = "文件") -> List[Dict[str, str]]:
    """
    從指定目錄加載文本文件
    
    Args:
        directory: 目錄路徑
        file_type: 文件類型描述（用於日誌）
        
    Returns:
        包含文件名和內容的字典列表
    """
    if not directory.exists():
        raise FileNotFoundError(f"{file_type}目錄不存在: {directory}")
    
    files_content = []
    for ext in ['*.txt', '*.md']:
        for file in directory.glob(ext):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # 跳過空文件
                        files_content.append({
                            'filename': file.name,
                            'content': content
                        })
                        logging.info(f"已加載{file_type}: {file.name} ({len(content)} 字元)")
            except Exception as e:
                logging.warning(f"無法讀取{file_type} {file}: {str(e)}")
    
    if not files_content:
        raise ValueError(f"在 {directory} 中找不到有效的{file_type}")
    
    return files_content


def extract_meeting_info(filename: str) -> tuple:
    """
    從文件名中提取會議編號和日期
    
    Args:
        filename: 文件名
        
    Returns:
        包含會議編號和日期的元組 (meeting_number, meeting_date)
    """
    import re
    # 匹配格式：第XXX次市政會議YYY年MM月DD日
    match = re.search(r'第(\d+)次市政會議(\d+)年(\d+)月(\d+)日', filename)
    if match:
        meeting_num = match.group(1)
        meeting_date = f"{match.group(2)}年{match.group(3)}月{match.group(4)}日"
        return (meeting_num, meeting_date)
    return (None, None)


def match_transcripts_with_references(transcripts: List[Dict], references: List[Dict]):
    """
    將逐字稿與參考會議記錄進行匹配
    
    Args:
        transcripts: 逐字稿列表
        references: 參考會議記錄列表
        
    Returns:
        匹配後的數據列表，每個元素包含對應的逐字稿和參考會議記錄
    """
    matched_data = []
    
    # 為所有參考文件建立索引 (meeting_num, meeting_date) -> reference
    ref_index = {}
    for ref in references:
        meeting_num, meeting_date = extract_meeting_info(ref['filename'])
        if meeting_num and meeting_date:
            ref_index[(meeting_num, meeting_date)] = ref
    
    # 匹配逐字稿和參考文件
    for transcript in transcripts:
        meeting_num, meeting_date = extract_meeting_info(transcript['filename'])
        
        if not meeting_num or not meeting_date:
            logging.warning(f"無法從文件名中提取會議信息: {transcript['filename']}")
            continue
            
        ref_key = (meeting_num, meeting_date)
        if ref_key in ref_index:
            ref = ref_index[ref_key]
            matched_data.append({
                'transcript': transcript['content'],
                'reference': ref['content'],
                'transcript_file': transcript['filename'],
                'reference_file': ref['filename']
            })
        else:
            logging.warning(f"未找到 {transcript['filename']} 的參考會議記錄")
    
    if not matched_data:
        raise ValueError("無法匹配逐字稿和參考會議記錄，請檢查文件名是否對應")
    return matched_data


def setup_logging(output_dir: Path) -> None:
    """設置日誌記錄"""
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 清除現有的日誌處理程序
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 配置日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件處理程序
    log_file = log_dir / "optimization.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(log_format)
    
    # 控制台處理程序
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    
    # 配置根日誌記錄器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        force=True
    )
    
    logging.info(f"日誌已初始化，日誌文件: {log_file.absolute()}")


def main():
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='會議記錄模板優化工具')
    parser.add_argument('--transcript-dir', type=str, required=True,
                      help='包含逐字稿的目錄')
    parser.add_argument('--reference-dir', type=str, required=True,
                      help='包含參考會議記錄的目錄')
    parser.add_argument('-o', '--output-dir', default='optimized_results',
                      help='輸出目錄（默認：optimized_results）')
    parser.add_argument('--model', default="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                      help='使用的模型名稱（默認：cwchang/llama3-taide-lx-8b-chat-alpha1:latest）')
    parser.add_argument('--max-iterations', type=int, default=100,
                      help='最大迭代次數（默認：100）')
    parser.add_argument('--batch-size', type=int, default=3,
                      help='批次大小（默認：3）')
    parser.add_argument('--warmup-iterations', type=int, default=2,
                      help='預熱迭代次數（默認：2）')
    parser.add_argument('--early-stopping', type=int, default=30,
                      help='早停輪數（默認：30）')
    parser.add_argument('--stability-threshold', type=float, default=0.7,
                      help='穩定性閾值（0-1，默認：0.7）')
    parser.add_argument('--quality-threshold', type=float, default=0.6,
                      help='質量閾值（0-1，默認：0.6）')
    parser.add_argument('--min-improvement', type=float, default=0.01,
                      help='最小改進閾值（默認：0.01）')
    
    args = parser.parse_args()
    
    # 設置輸出目錄
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 設置日誌
    setup_logging(output_dir)
    
    try:
        # 加載數據
        logging.info('正在加載逐字稿...')
        transcripts = load_text_files(Path(args.transcript_dir), "逐字稿")
        logging.info(f'成功加載 {len(transcripts)} 個逐字稿')
        
        logging.info('正在加載參考會議記錄...')
        references = load_text_files(Path(args.reference_dir), "參考會議記錄")
        logging.info(f'成功加載 {len(references)} 個參考會議記錄')
        
        # 匹配逐字稿和參考會議記錄
        matched_data = match_transcripts_with_references(transcripts, references)
        logging.info(f'成功匹配 {len(matched_data)} 對數據')
        
        # 初始化優化器
        from scripts.optimize_meeting_minutes import MeetingOptimizer
        
        optimizer = MeetingOptimizer(
            model_name=args.model,
            output_dir=str(output_dir)
        )
        
        # 執行優化
        logging.info('開始優化流程...')
        best_template, best_strategy, best_score = optimizer.optimize(
            matched_data=matched_data,
            max_iterations=args.max_iterations,
            batch_size=args.batch_size,
            warmup_iterations=args.warmup_iterations,
            early_stopping=args.early_stopping,
            min_improvement=args.min_improvement
        )
        
        logging.info(f'優化完成，最佳分數: {best_score:.4f}')
        logging.info(f'最佳模板:\n{best_template}')
        logging.info(f'最佳策略: {best_strategy}')
        
        # 顯示最佳模板
        logging.info("=" * 50)
        logging.info("\n最佳模板:")
        logging.info("-" * 50)
        logging.info(best_template)
        logging.info("-" * 50)
        
        return 0
        
    except Exception as e:
        logging.error(f'優化過程中出錯: {str(e)}', exc_info=True)
        return 1


if __name__ == "__main__":
    main()
