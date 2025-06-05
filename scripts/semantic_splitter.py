#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段模組 - 使用 Gemma3:12b 進行智能分段
處理超長逐字稿，確保分段的語意完整性
"""

import os
import json
import logging
import re
from typing import List, Dict, Tuple, Optional, Union, Any
from datetime import datetime
import requests

class SemanticSplitter:
    """語意分段器 - 使用 Gemma3 模型進行智能分段"""
    
    def __init__(self, 
                 model_name: str = "gemma3:12b",
                 ollama_url: str = "http://localhost:11434/api/generate",
                 max_segment_length: int = 4000,
                 overlap_length: int = 200):
        """
        初始化語意分段器
        
        Args:
            model_name: Ollama 模型名稱
            ollama_url: Ollama API 端點
            max_segment_length: 每段最大字元數
            overlap_length: 段落重疊字元數
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.max_segment_length = max_segment_length
        self.overlap_length = overlap_length
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger(f"SemanticSplitter_{self.model_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        """調用 Ollama API"""
        try:
            payload = {
                "model": self.model_name,
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
            return str(result.get("response", "")).strip()
            
        except Exception as e:
            self.logger.error(f"Ollama API 調用失敗: {e}")
            return ""
    
    def _find_natural_breakpoints(self, text: str, target_length: int) -> List[int]:
        """
        尋找自然分段點（段落、句號、換行等）
        
        Args:
            text: 要分段的文本
            target_length: 目標分段長度
            
        Returns:
            分段點位置列表
        """
        breakpoints = []
        
        # 優先級分段點
        patterns = [
            r'\n\n',  # 雙換行（段落分隔）
            r'。\s*\n',  # 句號後換行
            r'。\s+',  # 句號後空格
            r'！\s*\n',  # 驚嘆號後換行
            r'？\s*\n',  # 問號後換行
            r'，\s*\n',  # 逗號後換行
        ]
        
        current_pos = 0
        while current_pos < len(text):
            # 計算目標分段結束位置
            end_pos = min(current_pos + target_length, len(text))
            
            if end_pos >= len(text):
                breakpoints.append(len(text))
                break
                
            # 在目標範圍內尋找最佳分段點
            best_breakpoint = end_pos
            search_start = max(current_pos + target_length - 500, current_pos)
            search_text = text[search_start:end_pos + 200]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, search_text))
                if matches:
                    # 選擇最接近目標長度的分段點
                    for match in reversed(matches):
                        absolute_pos = search_start + match.end()
                        if absolute_pos > current_pos + 500:  # 最小分段長度
                            best_breakpoint = absolute_pos
                            break
                    break
            
            breakpoints.append(best_breakpoint)
            current_pos = best_breakpoint
            
        return breakpoints
    
    def _analyze_segment_coherence(self, segment: str) -> Dict[str, Union[float, List[str]]]:
        """
        使用 Gemma3 分析段落語意完整性
        
        Args:
            segment: 要分析的文本段落
            
        Returns:
            語意分析結果字典
        """
        analysis_prompt = f"""
請分析以下文本段落的語意完整性和內容品質：

文本段落：
{segment[:1000]}...

請從以下角度評分（0-10分）：
1. 語意完整性：段落開頭和結尾是否自然完整
2. 主題一致性：段落內容是否圍繞同一主題
3. 邏輯連貫性：內容邏輯是否清晰連貫
4. 資訊完整性：重要資訊是否被完整保留

請以JSON格式回答：
{{
    "semantic_completeness": 分數,
    "topic_consistency": 分數,
    "logical_coherence": 分數,
    "information_completeness": 分數,
    "overall_score": 總分,
    "issues": ["問題1", "問題2"],
    "suggestions": ["建議1", "建議2"]
}}
"""
        
        response = self._call_ollama(analysis_prompt, temperature=0.2)
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result: Dict[str, Union[float, List[str]]] = json.loads(json_match.group())
                return result
        except Exception as e:
            self.logger.warning(f"語意分析結果解析失敗: {e}")
            
        # 默認評分
        return {
            "semantic_completeness": 7.0,
            "topic_consistency": 7.0,
            "logical_coherence": 7.0,
            "information_completeness": 7.0,
            "overall_score": 7.0,
            "issues": [],
            "suggestions": []
        }
    
    def _optimize_segment_boundary(self, 
                                   text: str, 
                                   start_pos: int, 
                                   end_pos: int) -> Tuple[int, int]:
        """
        使用 Gemma3 優化分段邊界
        
        Args:
            text: 完整文本
            start_pos: 初始開始位置
            end_pos: 初始結束位置
            
        Returns:
            優化後的 (開始位置, 結束位置)
        """
        # 擴展分析範圍
        context_start = max(0, start_pos - 200)
        context_end = min(len(text), end_pos + 200)
        context = text[context_start:context_end]
        
        optimization_prompt = f"""
請幫助優化文本分段的邊界位置，確保語意完整性。

文本內容：
{context}

當前分段範圍：
- 開始位置（相對於上述文本）: {start_pos - context_start}
- 結束位置（相對於上述文本）: {end_pos - context_start}

請分析並建議更好的分段邊界，確保：
1. 段落在語意上完整
2. 避免在句子中間切斷
3. 保持主題的完整性

請以JSON格式回答：
{{
    "optimized_start": 相對開始位置,
    "optimized_end": 相對結束位置,
    "reason": "優化原因",
    "confidence": 信心度0-1
}}
"""
        
        response = self._call_ollama(optimization_prompt, temperature=0.1)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                new_start = context_start + result.get("optimized_start", start_pos - context_start)
                new_end = context_start + result.get("optimized_end", end_pos - context_start)
                
                # 邊界檢查
                new_start = max(0, min(new_start, len(text)))
                new_end = max(new_start + 100, min(new_end, len(text)))
                
                if result.get("confidence", 0) > 0.7:
                    return new_start, new_end
                    
        except Exception as e:
            self.logger.warning(f"邊界優化失敗: {e}")
            
        return start_pos, end_pos
    
    def split_text(self, text: str, enable_ai_optimization: bool = True) -> List[Dict]:
        """
        執行語意分段
        
        Args:
            text: 要分段的完整文本
            enable_ai_optimization: 是否啟用AI邊界優化
            
        Returns:
            分段結果列表，每個元素包含 segment_text, analysis, metadata
        """
        self.logger.info(f"開始語意分段，文本長度: {len(text)} 字元")
        
        if len(text) <= self.max_segment_length:
            # 文本太短，不需要分段
            analysis = self._analyze_segment_coherence(text)
            return [{
                "segment_id": 1,
                "segment_text": text,
                "analysis": analysis,
                "metadata": {
                    "start_pos": 0,
                    "end_pos": len(text),
                    "length": len(text),
                    "is_optimized": False
                }
            }]
        
        # 初步分段
        breakpoints = self._find_natural_breakpoints(text, self.max_segment_length)
        self.logger.info(f"找到 {len(breakpoints)} 個初步分段點")
        
        segments: List[Dict[str, Any]] = []
        for i, end_pos in enumerate(breakpoints):
            start_pos = 0 if i == 0 else breakpoints[i-1] - self.overlap_length
            start_pos = max(0, start_pos)
            
            # AI邊界優化
            if enable_ai_optimization and i > 0:
                original_start, original_end = start_pos, end_pos
                start_pos, end_pos = self._optimize_segment_boundary(text, start_pos, end_pos)
                is_optimized = (start_pos != original_start or end_pos != original_end)
            else:
                is_optimized = False
            
            # 提取分段文本
            segment_text = text[start_pos:end_pos].strip()
            
            if not segment_text:
                continue
                
            # 分析語意品質
            analysis = self._analyze_segment_coherence(segment_text)
            
            segment_info: Dict[str, Any] = {
                "segment_id": len(segments) + 1,
                "segment_text": segment_text,
                "analysis": analysis,
                "metadata": {
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "length": len(segment_text),
                    "is_optimized": is_optimized
                }
            }
            
            segments.append(segment_info)
            
            # 安全提取品質分數
            overall_score = analysis.get('overall_score', 0)
            quality_score = float(overall_score) if isinstance(overall_score, (int, float)) else 0.0
            
            self.logger.info(
                f"段落 {segment_info['segment_id']}: "
                f"長度={segment_info['metadata']['length']}, "
                f"品質={quality_score:.1f}/10"
            )
        
        self.logger.info(f"語意分段完成，共 {len(segments)} 個段落")
        return segments
    
    def save_segments(self, segments: List[Dict], output_dir: str) -> str:
        """
        保存分段結果
        
        Args:
            segments: 分段結果列表
            output_dir: 輸出目錄
            
        Returns:
            保存的文件路徑
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"semantic_segments_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 準備保存數據
        save_data = {
            "metadata": {
                "model_name": self.model_name,
                "max_segment_length": self.max_segment_length,
                "overlap_length": self.overlap_length,
                "timestamp": timestamp,
                "total_segments": len(segments)
            },
            "segments": segments
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"分段結果已保存至: {filepath}")
        return filepath


def main() -> None:
    """測試語意分段功能"""
    # 示例長文本
    sample_text = """
    會議開始時間為上午9點整，由張經理主持本次季度業務回顧會議。
    首先，張經理歡迎所有與會人員，並簡要介紹了會議議程。
    
    第一項議題是第三季度銷售業績回顧。
    李副理報告指出，本季度總銷售額達到2,500萬元，較去年同期成長15%。
    其中，線上銷售占比提升至40%，顯示數位轉型策略的成效。
    
    接下來討論的是產品開發進度。
    研發部王經理表示，新產品A已完成原型設計，預計下個月進入測試階段。
    產品B的市場調研也已完成，客戶反饋整體正面。
    
    財務部陳會計師報告了成本控制情況。
    本季度營運成本較預算節省8%，主要歸功於供應鏈優化和自動化流程導入。
    但需要注意原物料價格上漲的風險。
    
    人資部門提出了人才招募計畫。
    由於業務擴張需要，預計第四季度將新增20個職位。
    重點招募對象包括軟體工程師、數據分析師和業務代表。
    
    最後，張經理總結了會議要點，並安排下次會議時間。
    會議於上午11點30分結束，所有決議將以書面形式發送給與會人員。
    """ * 3  # 複製3次以增加長度
    
    # 初始化分段器
    splitter = SemanticSplitter(
        model_name="gemma3:12b",
        max_segment_length=1000,
        overlap_length=100
    )
    
    # 執行分段
    segments = splitter.split_text(sample_text)
    
    # 顯示結果
    print(f"\n=== 語意分段結果 ===")
    print(f"原文長度: {len(sample_text)} 字元")
    print(f"分段數量: {len(segments)}")
    
    for segment in segments:
        print(f"\n段落 {segment['segment_id']}:")
        print(f"  長度: {segment['metadata']['length']} 字元")
        print(f"  品質: {segment['analysis']['overall_score']:.1f}/10")
        print(f"  內容預覽: {segment['segment_text'][:100]}...")
    
    # 保存結果
    output_path = splitter.save_segments(segments, "tmp_staging")
    print(f"\n結果已保存至: {output_path}")


if __name__ == "__main__":
    main()
