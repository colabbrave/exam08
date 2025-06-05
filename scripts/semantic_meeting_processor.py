#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段會議記錄處理器
整合語意分段、品質評估和會議記錄生成的完整流程
"""

import os
import json
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
import requests

try:
    from .semantic_splitter import SemanticSplitter
    from .segment_quality_eval import SegmentQualityEvaluator
except ImportError:
    # 當作為腳本直接執行時的回退導入
    from semantic_splitter import SemanticSplitter
    from segment_quality_eval import SegmentQualityEvaluator


class SemanticMeetingProcessor:
    """語意分段會議記錄處理器"""
    
    def __init__(self, 
                 splitter_model: str = "gemma3:12b",
                 generator_model: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                 ollama_url: str = "http://localhost:11434/api/generate",
                 max_segment_length: int = 4000,
                 overlap_length: int = 200,
                 quality_threshold: float = 6.0):
        """
        初始化處理器
        
        Args:
            splitter_model: 語意分段模型
            generator_model: 會議記錄生成模型
            ollama_url: Ollama API 端點
            max_segment_length: 最大分段長度
            overlap_length: 段落重疊長度
            quality_threshold: 品質閾值
        """
        self.splitter_model = splitter_model
        self.generator_model = generator_model
        self.ollama_url = ollama_url
        self.quality_threshold = quality_threshold
        
        # 初始化組件
        self.splitter = SemanticSplitter(
            model_name=splitter_model,
            ollama_url=ollama_url,
            max_segment_length=max_segment_length,
            overlap_length=overlap_length
        )
        
        self.quality_evaluator = SegmentQualityEvaluator(
            model_name=splitter_model,
            ollama_url=ollama_url
        )
        
        self.logger = self._setup_logger()
        
        # 會議記錄生成提示詞模板
        self.meeting_prompt_template = """
請根據以下會議逐字稿片段，生成結構化的會議記錄：

逐字稿片段：
{transcript_segment}

請按照以下格式生成會議記錄：

## 會議片段摘要

### 主要討論議題
- 

### 重要決議
- 

### 行動項目
- 負責人：
- 期限：
- 內容：

### 關鍵數據或資訊
- 

### 參與人員發言要點
- 

請確保：
1. 保留重要的具體數據和時間
2. 突出明確的決議和行動項目
3. 組織清晰，條理分明
4. 使用專業的會議記錄語言
"""
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger("SemanticMeetingProcessor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _call_ollama(self, prompt: str, model: str, temperature: float = 0.3) -> str:
        """調用 Ollama API"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_predict": 4096
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            self.logger.error(f"Ollama API 調用失敗 (模型: {model}): {e}")
            return ""
    
    def _generate_segment_meeting_record(self, segment_text: str) -> str:
        """
        為單個段落生成會議記錄
        
        Args:
            segment_text: 段落文本
            
        Returns:
            生成的會議記錄片段
        """
        prompt = self.meeting_prompt_template.format(transcript_segment=segment_text)
        
        self.logger.info(f"正在生成會議記錄片段，文本長度: {len(segment_text)} 字元")
        
        # 使用會議記錄生成模型
        meeting_record = self._call_ollama(prompt, self.generator_model, temperature=0.2)
        
        if not meeting_record:
            self.logger.warning("會議記錄生成失敗，使用備用格式")
            meeting_record = f"""
## 會議片段摘要

### 主要內容
{segment_text[:500]}...

### 備註
此片段的會議記錄生成失敗，請手動處理。
"""
        
        return meeting_record
    
    def _merge_meeting_records(self, segment_records: List[Dict]) -> str:
        """
        整合所有段落的會議記錄
        
        Args:
            segment_records: 段落會議記錄列表
            
        Returns:
            完整的會議記錄
        """
        merge_prompt = f"""
請將以下多個會議記錄片段整合成一份完整、連貫的會議記錄：

{chr(10).join([f"=== 片段 {record['segment_id']} ==={chr(10)}{record['meeting_record']}{chr(10)}" for record in segment_records])}

請生成一份結構化的完整會議記錄，包含：

# 會議記錄

## 會議基本資訊
- 會議時間：
- 主持人：
- 參與人員：

## 會議議程與討論

### 第一項議題：
#### 討論內容
#### 決議事項
#### 行動項目

### 第二項議題：
#### 討論內容
#### 決議事項
#### 行動項目

## 重要決議彙整
1. 
2. 

## 後續行動項目
| 項目 | 負責人 | 期限 | 狀態 |
|------|--------|------|------|
|      |        |      |      |

## 下次會議安排
- 時間：
- 議題：

請確保：
1. 消除重複內容
2. 保持邏輯連貫性
3. 突出重要決議和行動項目
4. 使用專業的會議記錄格式
"""
        
        self.logger.info("正在整合所有會議記錄片段")
        
        # 使用會議記錄生成模型進行整合
        final_record = self._call_ollama(merge_prompt, self.generator_model, temperature=0.1)
        
        if not final_record:
            self.logger.warning("會議記錄整合失敗，使用簡單合併")
            final_record = "# 會議記錄\n\n" + "\n\n".join([
                f"## 片段 {record['segment_id']}\n{record['meeting_record']}" 
                for record in segment_records
            ])
        
        return final_record
    
    def process_transcript(self, 
                          transcript_text: str, 
                          output_dir: str = "output",
                          enable_quality_check: bool = True,
                          max_retry_attempts: int = 2) -> Dict:
        """
        處理會議逐字稿的完整流程
        
        Args:
            transcript_text: 會議逐字稿文本
            output_dir: 輸出目錄
            enable_quality_check: 是否啟用品質檢查
            max_retry_attempts: 最大重試次數
            
        Returns:
            處理結果字典
        """
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.logger.info(f"開始處理會議逐字稿，文本長度: {len(transcript_text)} 字元")
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        process_dir = os.path.join(output_dir, f"semantic_process_{timestamp}")
        os.makedirs(process_dir, exist_ok=True)
        
        result = {
            "timestamp": timestamp,
            "process_dir": process_dir,
            "original_length": len(transcript_text),
            "processing_steps": []
        }
        
        try:
            # 步驟1: 語意分段
            self.logger.info("步驟1: 執行語意分段")
            segments = self.splitter.split_text(transcript_text, enable_ai_optimization=True)
            
            # 保存分段結果
            segments_path = self.splitter.save_segments(segments, process_dir)
            result["segments_file"] = segments_path
            result["segment_count"] = len(segments)
            result["processing_steps"].append({
                "step": 1,
                "name": "語意分段",
                "status": "completed",
                "output": segments_path,
                "segment_count": len(segments)
            })
            
            # 步驟2: 品質評估（如果啟用）
            if enable_quality_check:
                self.logger.info("步驟2: 分段品質評估")
                evaluation_results = self.quality_evaluator.evaluate_segments(
                    segments, original_text=transcript_text
                )
                
                # 保存評估報告
                evaluation_path = self.quality_evaluator.save_evaluation_report(
                    evaluation_results, process_dir
                )
                result["evaluation_file"] = evaluation_path
                result["quality_score"] = evaluation_results["overall_quality"]["score"]
                result["quality_acceptable"] = evaluation_results["overall_quality"]["is_acceptable"]
                
                result["processing_steps"].append({
                    "step": 2,
                    "name": "品質評估",
                    "status": "completed",
                    "output": evaluation_path,
                    "quality_score": result["quality_score"],
                    "issues_count": len(evaluation_results["issues"])
                })
                
                # 品質檢查
                if result["quality_score"] < self.quality_threshold:
                    self.logger.warning(f"分段品質不達標 ({result['quality_score']:.2f} < {self.quality_threshold})")
                    
                    # 如果有改進建議且未達最大重試次數，可以考慮重新分段
                    if (max_retry_attempts > 0 and 
                        evaluation_results.get("improvement_suggestions")):
                        self.logger.info("嘗試根據建議優化分段...")
                        # 這裡可以實現基於建議的重新分段邏輯
                        # 為簡化，目前直接繼續處理
            
            # 步驟3: 生成會議記錄片段
            self.logger.info("步驟3: 生成會議記錄片段")
            segment_records = []
            
            for i, segment in enumerate(segments):
                self.logger.info(f"處理段落 {segment['segment_id']}/{len(segments)}")
                
                meeting_record = self._generate_segment_meeting_record(segment["segment_text"])
                
                segment_record = {
                    "segment_id": segment["segment_id"],
                    "original_text": segment["segment_text"],
                    "meeting_record": meeting_record,
                    "metadata": segment["metadata"],
                    "analysis": segment.get("analysis", {})
                }
                
                segment_records.append(segment_record)
            
            # 保存段落會議記錄
            segments_records_path = os.path.join(process_dir, "segment_meeting_records.json")
            with open(segments_records_path, 'w', encoding='utf-8') as f:
                json.dump(segment_records, f, ensure_ascii=False, indent=2)
            
            result["segment_records_file"] = segments_records_path
            result["processing_steps"].append({
                "step": 3,
                "name": "生成會議記錄片段",
                "status": "completed",
                "output": segments_records_path,
                "segments_processed": len(segment_records)
            })
            
            # 步驟4: 整合完整會議記錄
            self.logger.info("步驟4: 整合完整會議記錄")
            final_meeting_record = self._merge_meeting_records(segment_records)
            
            # 保存最終會議記錄
            final_record_path = os.path.join(process_dir, "final_meeting_record.md")
            with open(final_record_path, 'w', encoding='utf-8') as f:
                f.write(final_meeting_record)
            
            result["final_record_file"] = final_record_path
            result["final_record_length"] = len(final_meeting_record)
            result["processing_steps"].append({
                "step": 4,
                "name": "整合完整會議記錄",
                "status": "completed",
                "output": final_record_path,
                "record_length": len(final_meeting_record)
            })
            
            # 計算處理時間
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["status"] = "success"
            
            self.logger.info(f"處理完成，耗時: {processing_time:.2f} 秒")
            
            # 保存處理結果摘要
            summary_path = os.path.join(process_dir, "process_summary.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            result["summary_file"] = summary_path
            
        except Exception as e:
            self.logger.error(f"處理過程中發生錯誤: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            result["processing_time"] = time.time() - start_time
        
        return result
    
    def batch_process_files(self, 
                           input_dir: str, 
                           output_dir: str = "output",
                           file_pattern: str = "*.txt") -> List[Dict]:
        """
        批次處理多個逐字稿文件
        
        Args:
            input_dir: 輸入目錄
            output_dir: 輸出目錄
            file_pattern: 文件匹配模式
            
        Returns:
            批次處理結果列表
        """
        import glob
        
        files = glob.glob(os.path.join(input_dir, file_pattern))
        results = []
        
        self.logger.info(f"發現 {len(files)} 個文件待處理")
        
        for i, file_path in enumerate(files):
            self.logger.info(f"處理文件 {i+1}/{len(files)}: {os.path.basename(file_path)}")
            
            try:
                # 讀取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 處理文件
                result = self.process_transcript(content, output_dir)
                result["source_file"] = file_path
                result["file_index"] = i + 1
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"處理文件 {file_path} 時發生錯誤: {e}")
                results.append({
                    "source_file": file_path,
                    "file_index": i + 1,
                    "status": "error",
                    "error": str(e)
                })
        
        # 保存批次處理報告
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_report_path = os.path.join(output_dir, f"batch_report_{batch_timestamp}.json")
        
        batch_summary = {
            "timestamp": batch_timestamp,
            "total_files": len(files),
            "successful": len([r for r in results if r.get("status") == "success"]),
            "failed": len([r for r in results if r.get("status") == "error"]),
            "results": results
        }
        
        with open(batch_report_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"批次處理完成，報告保存至: {batch_report_path}")
        return results


def main():
    """測試語意分段會議記錄處理器"""
    # 示例會議逐字稿
    sample_transcript = """
    主持人：大家好，歡迎參加今天的第三季度業務回顧會議。今天是2024年10月15日，上午9點整。
    今天的會議主要討論三個議題：第三季度業績回顧、第四季度規劃，以及新產品開發進度。
    
    首先，請李副理報告第三季度的銷售業績。
    
    李副理：謝謝主持人。根據財務部門統計，第三季度總銷售額達到2,800萬元，較去年同期成長18%。
    其中，線上銷售占比提升至45%，較上季度增加5個百分點。主要成長動力來自新客戶開發和產品線擴充。
    
    但是我們也觀察到一些挑戰，原物料成本上漲了12%，對毛利率造成一定壓力。
    建議第四季度加強成本控制，同時評估價格調整的可能性。
    
    主持人：謝謝李副理的報告。請問財務部陳會計師對成本控制有什麼具體建議？
    
    陳會計師：關於成本控制，我們已經識別出三個主要方向。第一是供應鏈優化，
    與主要供應商重新談判合約，預估可節省5%的採購成本。第二是製程改善，
    導入自動化設備可降低人力成本約8%。第三是庫存管理精進，減少庫存積壓。
    
    這些措施預計在第四季度開始實施，明年第一季度就能看到效果。
    
    主持人：很好。接下來請研發部王經理報告新產品開發進度。
    
    王經理：新產品A的開發已經進入最後階段，預計11月底完成所有測試。
    市場調研顯示，目標客戶對產品特色反應積極，預估上市後6個月內可達到500萬銷售額。
    
    產品B目前遇到一些技術挑戰，主要是電池續航力還需要改善。
    我們正與供應商合作尋找解決方案，可能會延後2個月上市。
    
    主持人：關於產品B的延遲，對整體規劃有什麼影響？
    
    王經理：影響相對有限，因為產品A可以先填補市場空缺。但我們需要調整行銷預算分配，
    將原本分給產品B的資源暫時轉移到產品A的推廣上。
    
    主持人：好的，那我們現在決議幾個重要事項。第一，同意財務部提出的成本控制計畫，
    請陳會計師在下周五前提交詳細實施方案。第二，產品A按原定計畫推進，
    產品B則調整為明年第一季度上市。第三，第四季度業績目標維持3,200萬元不變。
    
    今天的會議就到這裡，下次會議時間訂在11月15日，同樣時間地點。謝謝大家。
    """ * 2  # 複製2次增加長度
    
    # 初始化處理器
    processor = SemanticMeetingProcessor(
        splitter_model="gemma3:12b",
        generator_model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
        max_segment_length=1500,
        overlap_length=150,
        quality_threshold=6.0
    )
    
    # 執行處理
    result = processor.process_transcript(
        sample_transcript,
        output_dir="tmp_staging",
        enable_quality_check=True
    )
    
    # 顯示結果
    print(f"\n=== 語意分段會議記錄處理結果 ===")
    print(f"狀態: {result['status']}")
    print(f"原文長度: {result['original_length']} 字元")
    print(f"分段數量: {result.get('segment_count', 0)}")
    print(f"品質分數: {result.get('quality_score', '未評估')}")
    print(f"處理時間: {result.get('processing_time', 0):.2f} 秒")
    print(f"輸出目錄: {result['process_dir']}")
    
    if result.get('final_record_file'):
        print(f"最終會議記錄: {result['final_record_file']}")
    
    # 顯示處理步驟
    print(f"\n處理步驟:")
    for step in result.get('processing_steps', []):
        print(f"  {step['step']}. {step['name']}: {step['status']}")


if __name__ == "__main__":
    main()
