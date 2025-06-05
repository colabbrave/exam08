#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段批次處理與報告生成
自動處理逐字稿並生成品質檢查報告
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加專案根目錄到路徑
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from scripts.semantic_splitter import SemanticSplitter
    from scripts.segment_quality_eval import SegmentQualityEvaluator
    from scripts.semantic_meeting_processor import SemanticMeetingProcessor
    SEMANTIC_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 無法載入語意分段模組 ({e})")
    SEMANTIC_MODULES_AVAILABLE = False

class BatchSemanticProcessor:
    """批次語意分段處理器"""
    
    def __init__(self, 
                 segmentation_model: str = "gemma3:12b",
                 evaluation_model: str = "gemma3:12b",
                 output_dir: str = "output"):
        """
        初始化批次處理器
        
        Args:
            segmentation_model: 分段模型名稱
            evaluation_model: 評估模型名稱  
            output_dir: 輸出目錄
        """
        self.segmentation_model = segmentation_model
        self.evaluation_model = evaluation_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 設置日誌
        self.logger = self._setup_logger()
        
        # 初始化組件
        if SEMANTIC_MODULES_AVAILABLE:
            self.splitter = SemanticSplitter(
                model_name=segmentation_model,
                max_segment_length=4000,
                overlap_length=200
            )
            self.evaluator = SegmentQualityEvaluator(
                model_name=evaluation_model
            )
            self.processor = SemanticMeetingProcessor(
                splitter_model=segmentation_model,
                generator_model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest"
            )
            self.logger.info("語意分段模組初始化成功")
        else:
            self.splitter = None
            self.evaluator = None
            self.processor = None
            self.logger.error("語意分段模組不可用")
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger("BatchSemanticProcessor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台處理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件處理器
            log_file = self.output_dir / f"batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
    
    def process_transcript_file(self, transcript_path: str) -> Dict:
        """
        處理單個逐字稿文件
        
        Args:
            transcript_path: 逐字稿文件路徑
            
        Returns:
            處理結果字典
        """
        if not SEMANTIC_MODULES_AVAILABLE or self.splitter is None or self.evaluator is None:
            return {"error": "語意分段模組不可用"}
            
        path_obj = Path(transcript_path)
        if not path_obj.exists():
            return {"error": f"文件不存在: {transcript_path}"}
        
        self.logger.info(f"開始處理逐字稿: {transcript_path}")
        
        try:
            # 讀取逐字稿
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_content = f.read()
            
            file_size = len(transcript_content)
            self.logger.info(f"文件大小: {file_size} 字元")
            
            # 檢查是否需要分段
            if file_size < 4000:
                self.logger.info("文件較小，無需分段處理")
                return {
                    "file_path": str(transcript_path),
                    "file_size": file_size,
                    "needs_segmentation": False,
                    "processed_segments": None,
                    "quality_report": None
                }
            
            # 執行語意分段
            self.logger.info("執行語意分段...")
            segments = self.splitter.split_text(transcript_content)
            
            if not segments or not isinstance(segments, list):
                return {
                    "file_path": str(transcript_path),
                    "file_size": file_size,
                    "error": "分段失敗",
                    "segmentation_result": segments
                }
            self.logger.info(f"分段完成，共 {len(segments)} 個片段")
            
            # 執行品質評估
            self.logger.info("執行品質評估...")
            quality_report = self.evaluator.batch_quality_check(segments)
            
            # 生成詳細報告
            processing_result = {
                "file_path": str(transcript_path),
                "file_size": file_size,
                "processing_timestamp": datetime.now().isoformat(),
                "needs_segmentation": True,
                "segment_count": len(segments),
                "segmentation_result": segments,
                "quality_report": quality_report,
                "overall_quality_score": quality_report["summary"]["overall_quality"],
                "needs_revision": quality_report["summary"]["needs_revision"],
                "revision_suggestions": quality_report["summary"]["revision_suggestions"]
            }
            
            # 儲存處理結果
            result_file = self.output_dir / f"processing_result_{path_obj.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(processing_result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"處理完成，整體品質分數: {quality_report['summary']['overall_quality']:.2f}")
            self.logger.info(f"結果已儲存到: {result_file}")
            
            return processing_result
            
        except Exception as e:
            self.logger.error(f"處理逐字稿時發生錯誤: {e}", exc_info=True)
            return {
                "file_path": str(transcript_path),
                "error": str(e),
                "processing_timestamp": datetime.now().isoformat()
            }
    
    def batch_process_directory(self, transcript_dir: str) -> Dict:
        """
        批次處理目錄中的所有逐字稿
        
        Args:
            transcript_dir: 逐字稿目錄路徑
            
        Returns:
            批次處理總結報告
        """
        transcript_dir_path = Path(transcript_dir)
        if not transcript_dir_path.exists():
            self.logger.error(f"目錄不存在: {transcript_dir}")
            return {"error": f"目錄不存在: {transcript_dir}"}
        
        # 找到所有逐字稿文件
        transcript_files = list(transcript_dir_path.glob("*.txt"))
        self.logger.info(f"找到 {len(transcript_files)} 個逐字稿文件")
        
        if not transcript_files:
            self.logger.warning("目錄中沒有找到逐字稿文件")
            return {"warning": "沒有找到逐字稿文件"}
        
        # 批次處理
        batch_results = []
        successful_count = 0
        failed_count = 0
        
        for transcript_file in transcript_files:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"處理文件 {len(batch_results)+1}/{len(transcript_files)}: {transcript_file.name}")
            self.logger.info(f"{'='*60}")
            
            result = self.process_transcript_file(str(transcript_file))
            batch_results.append(result)
            
            if "error" in result:
                failed_count += 1
                self.logger.error(f"處理失敗: {result['error']}")
            else:
                successful_count += 1
                self.logger.info("處理成功")
        
        # 生成批次處理總結報告
        batch_summary = self._generate_batch_summary(batch_results, successful_count, failed_count)
        
        # 儲存總結報告
        summary_file = self.output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("批次處理完成")
        self.logger.info(f"成功: {successful_count}, 失敗: {failed_count}")
        self.logger.info(f"總結報告已儲存到: {summary_file}")
        self.logger.info(f"{'='*60}")
        
        return batch_summary
    
    def _generate_batch_summary(self, batch_results: List[Dict], 
                               successful_count: int, failed_count: int) -> Dict:
        """生成批次處理總結報告"""
        # 統計資料
        total_files = len(batch_results)
        segmented_files = len([r for r in batch_results if r.get("needs_segmentation", False)])
        
        # 品質統計
        quality_scores = [r.get("overall_quality_score", 0) for r in batch_results 
                         if "overall_quality_score" in r]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # 問題統計
        files_needing_revision = len([r for r in batch_results if r.get("needs_revision", False)])
        
        # 所有修訂建議
        all_suggestions = []
        for result in batch_results:
            if "revision_suggestions" in result:
                all_suggestions.extend(result["revision_suggestions"])
        
        # 建議統計
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1
        
        return {
            "batch_processing_timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_files": total_files,
                "successful_processing": successful_count,
                "failed_processing": failed_count,
                "files_requiring_segmentation": segmented_files,
                "files_needing_revision": files_needing_revision
            },
            "quality_analysis": {
                "average_quality_score": avg_quality,
                "quality_scores": quality_scores,
                "revision_rate": files_needing_revision / total_files * 100 if total_files > 0 else 0
            },
            "common_suggestions": dict(sorted(suggestion_counts.items(), 
                                            key=lambda x: x[1], reverse=True)),
            "detailed_results": batch_results
        }

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="語意分段批次處理與報告生成")
    parser.add_argument("--input-dir", default="data/transcript", 
                       help="逐字稿輸入目錄 (預設: data/transcript)")
    parser.add_argument("--output-dir", default="output", 
                       help="輸出目錄 (預設: output)")
    parser.add_argument("--segmentation-model", default="gemma3:12b",
                       help="分段模型 (預設: gemma3:12b)")
    parser.add_argument("--evaluation-model", default="gemma3:12b",
                       help="評估模型 (預設: gemma3:12b)")
    parser.add_argument("--single-file", 
                       help="處理單個文件而非整個目錄")
    
    args = parser.parse_args()
    
    # 初始化處理器
    processor = BatchSemanticProcessor(
        segmentation_model=args.segmentation_model,
        evaluation_model=args.evaluation_model,
        output_dir=args.output_dir
    )
    
    if args.single_file:
        # 處理單個文件
        result = processor.process_transcript_file(args.single_file)
        print(f"\n處理結果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 批次處理目錄
        result = processor.batch_process_directory(args.input_dir)
        print(f"\n批次處理總結:")
        print(json.dumps(result.get("statistics", {}), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
