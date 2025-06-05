#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
會議記錄優化與評估系統 - 核心優化引擎
依據 act.md 流程實現完整的疊代優化、評分、策略管理、early stopping
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import re
import requests
from glob import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# 專案根目錄設定
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 導入評估配置
try:
    from scripts.evaluation.config import EvaluationConfig  # type: ignore
except ImportError:
    # 如果找不到，嘗試從當前目錄
    try:
        from evaluation.config import EvaluationConfig  # type: ignore
    except ImportError:
        # 創建基本配置類
        class EvaluationConfig:
            def __init__(self):
                pass

# 導入語意分段相關模組
SEMANTIC_MODULES_AVAILABLE = False
SemanticSplitter = None
SegmentQualityEvaluator = None
SemanticMeetingProcessor = None

# 確保當前目錄在路徑中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # 首先嘗試從當前目錄導入（scripts/目錄內）
    from semantic_splitter import SemanticSplitter
    from segment_quality_eval import SegmentQualityEvaluator
    from semantic_meeting_processor import SemanticMeetingProcessor
    SEMANTIC_MODULES_AVAILABLE = True
    print("成功載入語意分段模組")
except ImportError as e1:
    try:
        # 嘗試從 scripts 包導入
        from scripts.semantic_splitter import SemanticSplitter
        from scripts.segment_quality_eval import SegmentQualityEvaluator
        from scripts.semantic_meeting_processor import SemanticMeetingProcessor
        SEMANTIC_MODULES_AVAILABLE = True
        print("成功載入語意分段模組（從scripts包）")
    except ImportError as e2:
        print(f"警告: 無法載入語意分段模組。第一次嘗試錯誤: {e1}, 第二次嘗試錯誤: {e2}")
        print("大型文本將使用標準處理")
        SEMANTIC_MODULES_AVAILABLE = False

# 導入評估模組
EVALUATOR_AVAILABLE = False
try:
    # 首先嘗試從當前目錄導入
    from evaluation import MeetingEvaluator, EvaluationConfig as EvalConfig
    EVALUATOR_AVAILABLE = True
    print("成功載入評估模組（從當前目錄）")
except ImportError as e1:
    try:
        # 嘗試從 scripts 包導入
        from scripts.evaluation import MeetingEvaluator, EvaluationConfig as EvalConfig
        EVALUATOR_AVAILABLE = True
        print("成功載入評估模組（從scripts包）")
    except ImportError as e2:
        print(f"警告: 無法載入評估模組。第一次嘗試錯誤: {e1}, 第二次嘗試錯誤: {e2}")
        print("將建立基本評估功能")
        EVALUATOR_AVAILABLE = False

def get_evaluator_class():
    """取得 MeetingEvaluator 類別"""
    if EVALUATOR_AVAILABLE:
        from scripts.evaluation import MeetingEvaluator
        return MeetingEvaluator
    else:
        # 建立基本評估功能類別
        class BasicEvaluator:
            def __init__(self):
                pass
            
            def evaluate(self, generated_text: str, reference_text: str) -> Dict[str, float]:
                """基本評估功能，返回固定分數"""
                return {
                    'overall_score': 0.5,
                    'bertscore': 0.5,
                    'taiwanscore': 0.5
                }
        return BasicEvaluator

@dataclass
class OptimizationResult:
    """優化結果資料結構"""
    iteration: int
    strategy_combination: List[str]
    minutes_content: str
    scores: Dict[str, float]
    execution_time: float
    timestamp: str
    model_used: str

@dataclass
class OptimizationConfig:
    """優化配置"""
    max_iterations: int = 5
    quality_threshold: float = 0.8
    min_improvement: float = 0.02
    strategy_max_count: int = 3
    model_name: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest"
    optimization_model: str = "gemma3:12b"
    enable_early_stopping: bool = True
    save_all_iterations: bool = True
    # 語意分段相關配置
    enable_semantic_segmentation: bool = True
    max_segment_length: int = 4000
    segment_overlap: int = 200
    semantic_model: str = "gemma3:12b"
    quality_threshold_semantic: float = 6.0

evaluator_class = get_evaluator_class()

class StrategyConfig:
    """Strategy configuration"""
    def __init__(self, name: str, description: str, components: Dict[str, Any], 
                 format_requirements: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.components = components
        self.format_requirements = format_requirements or {}

class MeetingOptimizer:
    """Meeting minutes optimizer"""
    
    def __init__(self, model_name: str = "cwchang/llama3-taide-lx-8b-chat-alpha1:latest", 
                 output_dir: Optional[str] = None,
                 strategy_config_path: Optional[Path] = None,
                 log_file: Optional[str] = None,
                 enable_semantic_segmentation: bool = True):
        """Initialize the meeting optimizer"""
        self.model_name = model_name
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "results/optimized"
        self.evaluator = evaluator_class()
        self.strategies: Dict[str, StrategyConfig] = {}
        self.enable_semantic_segmentation = enable_semantic_segmentation

        # 初始化語意分段相關組件
        self.config_manager = None
        self.semantic_splitter = None
        self.quality_evaluator = None
        self.semantic_processor = None
        self.logger_semantic = logging.getLogger("SemanticSegmentation")
        
        if SEMANTIC_MODULES_AVAILABLE and enable_semantic_segmentation:
            try:
                if (SemanticSplitter is not None and 
                    SegmentQualityEvaluator is not None and 
                    SemanticMeetingProcessor is not None):
                    
                    self.semantic_splitter = SemanticSplitter(
                        model_name="gemma3:12b",
                        max_segment_length=4000,
                        overlap_length=200
                    )
                    self.quality_evaluator = SegmentQualityEvaluator(
                        model_name="gemma3:12b"
                    )
                    self.semantic_processor = SemanticMeetingProcessor(
                        splitter_model="gemma3:12b",
                        generator_model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                        max_segment_length=4000,
                        overlap_length=200,
                        quality_threshold=6.0
                    )
                    self.logger_semantic.info("語意分段功能已啟用")
                else:
                    raise ImportError("語意分段模組類別不可用")
            except Exception as e:
                self.logger_semantic.warning(f"語意分段初始化失敗: {e}，將使用標準處理")
                self.enable_semantic_segmentation = False
                # 重置為 None
                self.config_manager = None
                self.semantic_splitter = None
                self.quality_evaluator = None
                self.semantic_processor = None
        else:
            self.enable_semantic_segmentation = False

        # Logger 設定
        self.logger = logging.getLogger("MeetingOptimizer")
        self.logger.setLevel(logging.DEBUG)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        # log file 路徑
        log_path = Path(log_file) if log_file else (self.output_dir.parent / "logs" / "optimization_debug.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 檔案處理器
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info(f"使用 Ollama 模型: {model_name}")
        
        # 初始化默認模板
        self.default_template = """[會議記錄]
會議主題: {topic}
與會人員: {participants}
會議時間: {time}

討論要點:
{key_points}

決議事項:
{decisions}

行動項目:
{action_items}"""

        # 創建輸出目錄
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 修正 _load_strategies 需 Path 型別
        config_path = Path(strategy_config_path) if strategy_config_path else Path(project_root) / "config" / "improvement_strategies.json"
        self._load_strategies(config_path)

    def _load_strategies(self, config_path: Path) -> None:
        """Load strategies from configuration file"""
        if not config_path.exists():
            self.logger.warning(f"策略配置文件 {config_path} 未找到，使用默認策略")
            self._load_default_strategies()
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                strategies_data = json.load(f)
            
            if not isinstance(strategies_data, dict):
                raise ValueError(f"配置文件中應為字典，但找到 {type(strategies_data).__name__}")
                
            loaded_count = 0
            for strategy_id, strategy_data in strategies_data.items():
                # 跳過 metadata 部分
                if strategy_id == 'metadata':
                    continue
                    
                try:
                    if not isinstance(strategy_data, dict):
                        self.logger.warning(f"跳過策略 {strategy_id}: 應為字典，但找到 {type(strategy_data).__name__}")
                        continue
                        
                    required_fields = ['name', 'description', 'components']
                    for field in required_fields:
                        if field not in strategy_data:
                            raise ValueError(f"策略 {strategy_id} 中缺少必要字段 '{field}'")
                    
                    self.strategies[strategy_id] = StrategyConfig(
                        name=str(strategy_data['name']),
                        description=str(strategy_data['description']),
                        components=dict(strategy_data['components']),
                        format_requirements=dict(strategy_data.get('format_requirements', {}))
                    )
                    loaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"加載策略 {strategy_id} 時出錯: {str(e)}")
                    continue
                    
            self.logger.info(f"已從 {config_path} 加載 {loaded_count} 個策略")
            
        except Exception as e:
            self.logger.error(f"從 {config_path} 加載策略失敗: {str(e)}")
            self._load_default_strategies()
    
    def _load_default_strategies(self) -> None:
        """Load default strategies when config file is not available"""
        self.strategies = {
            "default": StrategyConfig(
                name="默認策略",
                description="默認優化策略",
                components={
                    "summarization": {"enabled": True, "max_length": 500},
                    "key_points": {"enabled": True, "count": 5},
                    "action_items": {"enabled": True}
                },
                format_requirements={"required_sections": ["標準化術語表"]}
            ),
            "structured": StrategyConfig(
                name="結構化摘要",
                description="將會議記錄依議題、決議、待辦事項等分類，提升可讀性。",
                components={
                    "format": "markdown",
                    "sections": ["議題", "討論內容", "決議事項", "待辦事項"]
                },
                format_requirements={"required_sections": ["議題", "決議事項"]}
            )
        }
        self.logger.info("已加載默認策略")
    
    def _check_and_segment_transcript(self, transcript: str, transcript_file: str = "") -> List[Dict[str, Any]]:
        """
        檢查逐字稿長度，如需要則進行語意分段
        
        Args:
            transcript: 逐字稿內容
            transcript_file: 逐字稿檔案名稱
            
        Returns:
            List[Dict]: 分段結果，每個dict包含 'content', 'start_pos', 'end_pos' 等信息
        """
        # 檢查文本長度是否需要分段
        max_length = 4000  # 預設最大長度
        
        if len(transcript) <= max_length:
            self.logger.info(f"文本長度 {len(transcript)} 字元，無需分段")
            return [{
                'content': transcript,
                'start_pos': 0,
                'end_pos': len(transcript),
                'segment_id': 0,
                'is_segmented': False
            }]
        
        self.logger.info(f"文本長度 {len(transcript)} 字元，超過閾值 {max_length}，開始語意分段")
        
        if not self.enable_semantic_segmentation or not self.semantic_splitter:
            self.logger.warning("語意分段功能未啟用，使用簡單分段")
            return self._simple_segment(transcript, max_length)
        
        try:
            # 使用語意分段器
            segments = self.semantic_splitter.split_text(transcript)
            
            # 品質評估
            if self.quality_evaluator:
                quality_result = self.quality_evaluator.evaluate_segments(segments, transcript)
                quality_score = quality_result.get('overall_score', 0)
                quality_threshold = 6.0  # 固定閾值
                
                if quality_score < quality_threshold:
                    self.logger.warning(f"語意分段品質不佳 ({quality_score:.2f} < {quality_threshold})，使用簡單分段")
                    return self._simple_segment(transcript, max_length)
            
            # 轉換為標準格式
            segmented_results = []
            for i, segment in enumerate(segments):
                segmented_results.append({
                    'content': segment.get('segment_text', segment.get('content', '')),
                    'start_pos': segment.get('metadata', {}).get('start_pos', 0),
                    'end_pos': segment.get('metadata', {}).get('end_pos', 0),
                    'segment_id': i,
                    'is_segmented': True,
                    'quality_score': segment.get('analysis', {}).get('overall_score', 0)
                })
            
            self.logger.info(f"語意分段完成，共 {len(segmented_results)} 個分段")
            return segmented_results
            
        except Exception as e:
            self.logger.error(f"語意分段失敗: {e}，回退到簡單分段")
            return self._simple_segment(transcript, max_length)
            self.logger.error(f"語意分段失敗: {e}，回退到簡單分段")
            return self._simple_segment(transcript, max_length)
    
    def _simple_segment(self, text: str, max_length: int) -> List[Dict[str, Any]]:
        """簡單的文本分段方法"""
        segments = []
        overlap = 200  # 重疊長度
        
        start = 0
        segment_id = 0
        
        while start < len(text):
            # 如果剩餘內容小於max_length，直接處理完整剩餘部分
            remaining_length = len(text) - start
            if remaining_length <= max_length:
                segment_content = text[start:].strip()
                if segment_content:
                    segments.append({
                        'content': segment_content,
                        'start_pos': start,
                        'end_pos': len(text),
                        'segment_id': segment_id,
                        'is_segmented': True,
                        'method': 'simple'
                    })
                break
            
            end = min(start + max_length, len(text))
            
            # 嘗試在自然分段點分割
            if end < len(text):
                # 尋找最後的句號、問號或驚嘆號
                for i in range(end - 1, max(start, end - 200), -1):
                    if text[i] in '。？！\n':
                        end = i + 1
                        break
            
            segment_content = text[start:end].strip()
            if segment_content:
                segments.append({
                    'content': segment_content,
                    'start_pos': start,
                    'end_pos': end,
                    'segment_id': segment_id,
                    'is_segmented': True,
                    'method': 'simple'
                })
                segment_id += 1
            
            # 計算下一個開始位置，考慮重疊
            # 增加防呆機制：確保至少前進100字符以避免無限循環
            next_start = max(end - overlap, start + 100)
            
            # 如果下次開始位置沒有有效前進，強制前進
            if next_start <= start:
                next_start = start + max_length // 2
            
            start = next_start
            
            # 雙重檢查：如果開始位置超過文本長度，退出
            if start >= len(text):
                break
        
        self.logger.info(f"簡單分段完成，共 {len(segments)} 個分段")
        return segments

    def _process_segmented_transcript(self, segments: List[Dict[str, Any]], 
                                    template: str, strategy: Dict[str, Any]) -> List[str]:
        """
        處理分段的逐字稿，生成各段會議記錄
        
        Args:
            segments: 分段結果
            template: 使用的模板
            strategy: 使用的策略
            
        Returns:
            List[str]: 各段生成的會議記錄
        """
        if not segments:
            return []
        
        # 如果只有一個段落且未分段，直接處理
        if len(segments) == 1 and not segments[0].get('is_segmented', False):
            return self._generate_minutes_batch([{
                'transcript': segments[0]['content'],
                'transcript_file': '',
                'reference': segments[0]['content'],
                'reference_file': ''
            }], template, strategy)
        
        # 處理多個分段
        segment_minutes = []
        for i, segment in enumerate(segments):
            self.logger.info(f"處理第 {i+1}/{len(segments)} 個分段 (長度: {len(segment['content'])} 字元)")
            
            try:
                # 為每個分段生成會議記錄
                batch_data = [{
                    'transcript': segment['content'],
                    'transcript_file': f"segment_{segment['segment_id']}",
                    'reference': segment['content'],
                    'reference_file': ''
                }]
                
                generated = self._generate_minutes_batch(batch_data, template, strategy)
                if generated and generated[0].strip():
                    segment_minutes.append(generated[0])
                else:
                    self.logger.warning(f"第 {i+1} 段生成失敗，跳過")
                    
            except Exception as e:
                self.logger.error(f"處理第 {i+1} 段時發生錯誤: {e}")
                continue
        
        return segment_minutes
    
    def _merge_segment_minutes(self, segment_minutes: List[str], 
                             original_transcript: str = "") -> str:
        """
        整合多個分段的會議記錄為完整記錄
        
        Args:
            segment_minutes: 各段會議記錄
            original_transcript: 原始逐字稿（可選）
            
        Returns:
            str: 整合後的完整會議記錄
        """
        if not segment_minutes:
            return ""
        
        if len(segment_minutes) == 1:
            return segment_minutes[0]
        
        self.logger.info(f"整合 {len(segment_minutes)} 個分段的會議記錄")
        
        # 如果啟用了語意處理器，使用它來整合
        if self.enable_semantic_segmentation and self.semantic_processor:
            try:
                # 轉換為語意處理器期望的格式
                segment_records = []
                for i, minutes in enumerate(segment_minutes):
                    segment_records.append({
                        'meeting_record': minutes,  # 修正鍵名
                        'segment_id': i,
                        'metadata': {}
                    })
                
                merged_minutes = self.semantic_processor._merge_meeting_records(segment_records)
                self.logger.info("使用語意處理器成功整合會議記錄")
                return merged_minutes
            except Exception as e:
                self.logger.error(f"語意整合失敗: {e}，使用簡單整合")
        
        # 簡單整合方法
        return self._simple_merge_minutes(segment_minutes)
    
    def _simple_merge_minutes(self, segment_minutes: List[str]) -> str:
        """簡單的會議記錄整合方法"""
        # 提取各段的主要部分
        merged_content = {
            'topics': [],
            'discussions': [],
            'decisions': [],
            'actions': []
        }
        
        for i, minutes in enumerate(segment_minutes):
            # 簡單的內容提取
            lines = minutes.split('\n')
            current_section = 'discussions'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 判斷段落類型
                if any(keyword in line for keyword in ['主題', '議題']):
                    current_section = 'topics'
                elif any(keyword in line for keyword in ['決議', '決定', '結論']):
                    current_section = 'decisions'
                elif any(keyword in line for keyword in ['行動', '待辦', '執行']):
                    current_section = 'actions'
                elif any(keyword in line for keyword in ['討論', '說明', '報告']):
                    current_section = 'discussions'
                
                # 添加內容
                if line not in merged_content[current_section]:
                    merged_content[current_section].append(line)
        
        # 生成整合後的會議記錄
        result = "# 整合會議記錄\n\n"
        
        if merged_content['topics']:
            result += "## 會議主題\n" + "\n".join(merged_content['topics']) + "\n\n"
        
        if merged_content['discussions']:
            result += "## 討論內容\n" + "\n".join(merged_content['discussions']) + "\n\n"
        
        if merged_content['decisions']:
            result += "## 決議事項\n" + "\n".join(merged_content['decisions']) + "\n\n"
        
        if merged_content['actions']:
            result += "## 行動項目\n" + "\n".join(merged_content['actions']) + "\n\n"
        
        return result.strip()

    def optimize(self, matched_data: List[Dict], max_iterations: int = 2,
                batch_size: int = 3, warmup_iterations: int = 2,
                early_stopping: int = 30, min_improvement: float = 0.01) -> Tuple[str, Dict[str, float], float]:
        """
        執行完整的優化流程，嘗試多組模板與提示，根據評分自動選優
        
        Args:
            matched_data: 匹配的逐字稿和參考會議記錄列表
            max_iterations: 最大迭代次數
            batch_size: 每批處理的數據量
            warmup_iterations: 預熱迭代次數
            early_stopping: 早停輪數
            min_improvement: 最小改進閾值
            
        Returns:
            tuple: (最佳模板, 最佳策略, 最佳分數)
        """
        self.logger.info(f"開始優化流程，共 {len(matched_data)} 組數據")
        self.logger.debug(f"[DEBUG] optimize() matched_data: {json.dumps(matched_data, ensure_ascii=False)[:1000]}")
        # 多組模板
        template_candidates = [
            self.default_template,
            """# 會議記錄\n\n**主題：** {topic}\n**時間：** {time}\n**與會人員：** {participants}\n\n## 討論要點\n{key_points}\n\n## 決議事項\n{decisions}\n\n## 行動項目\n{action_items}""",
            """[會議摘要]\n主題: {topic}\n時間: {time}\n人員: {participants}\n重點: {key_points}\n決議: {decisions}\n行動: {action_items}"""
        ]
        best_template = template_candidates[0]
        best_score = 0.0
        best_metrics = {}
        best_minutes = None
        current_template = self.default_template
        current_strategy = {}
        for iteration in range(max_iterations):  # 依 max_iterations 疊代
            self.logger.info(f"\n=== 迭代 {iteration + 1}/{max_iterations} ===")
            # 強制 flush logger，確保 log 立即寫入
            for handler in self.logger.handlers:
                handler.flush()
            # 本輪只用一個 template（可改為多個）
            generated = self._generate_minutes_batch(
                matched_data[:batch_size],
                current_template,
                current_strategy
            )
            scores = self._evaluate_minutes_batch(
                generated,
                [d['reference'] for d in matched_data[:batch_size]]
            )
            
            # 使用 overall_score 作為主要評分，如果沒有則嘗試其他分數
            overall_score = scores.get("overall_score", 0)
            if overall_score == 0:
                # 如果沒有 overall_score，嘗試使用其他可用分數
                bert_score = scores.get("semantic_similarity_score", 0)
                content_score = scores.get("content_coverage_score", 0)
                structure_score = scores.get("structure_quality_score", 0)
                weighted_score = (bert_score * 0.5 + content_score * 0.3 + structure_score * 0.2)
            else:
                weighted_score = overall_score
                
            self.logger.info(f"[TEMPLATE] 疊代 {iteration+1} 綜合分數 (overall_score)={weighted_score:.4f} (詳細分數: {scores})")
            
            if (
                weighted_score > best_score + min_improvement
                and generated
                and generated[0].strip()
                and not generated[0].strip().startswith('{')
                and generated[0].strip() != current_template.strip()
            ):
                best_score = weighted_score
                best_template = current_template
                best_metrics = dict(scores)
                best_minutes = generated[0]
                self.logger.info(f"[TEMPLATE] 發現新最佳 minutes (綜合分數={weighted_score:.4f})")
            # 儲存本輪最佳 minutes
            if best_minutes:
                self._save_best_minutes(best_minutes, best_metrics, best_score)
            # 呼叫 LLM refine template/strategy
            transcript = matched_data[0]["transcript"]
            reference = matched_data[0]["reference"]
            new_template, new_strategy = self._refine_template_and_strategy_with_llm(transcript, best_minutes or generated[0], reference)
            if new_template:
                self.logger.info("[LLM] 疊代取得新 template，將用於下輪。")
                current_template = new_template
            if new_strategy:
                self.logger.info(f"[LLM] 疊代取得新策略建議: {new_strategy}")
                current_strategy = new_strategy
            # 強制 flush logger，確保 log 即時寫入
            for handler in self.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        # 回傳最佳 minutes 內容（非模板）
        return best_minutes if best_minutes else best_template, best_metrics, best_score
    
    def _generate_minutes_batch(self, data: List[Dict], template: str,
                             strategy: Dict) -> List[str]:
        """批量生成會議記錄，呼叫 Ollama LLM"""
        import requests
        
        results = []
        for idx, item in enumerate(data):
            transcript = item.get('transcript', '')
            transcript_file = item.get('transcript_file', '')

            try:
                # 檢查是否需要語意分段處理
                segmentation_result = self._check_and_segment_transcript(transcript)
                
                # 如果分段處理成功，處理分段結果
                if isinstance(segmentation_result, list) and len(segmentation_result) > 1:
                    # 分段處理：為每個分段生成會議記錄片段，然後整合
                    self.logger.info(f"檢測到大型文本，使用語意分段處理 ({len(segmentation_result)} 個分段)")
                    segment_minutes = self._process_segmented_transcript(segmentation_result, template, strategy)
                    final_minutes = self._merge_segment_minutes(segment_minutes, transcript)
                    results.append(final_minutes)
                    continue
                else:
                    # 使用原始或簡單分段的文本
                    processed_transcript = segmentation_result[0]['content'] if isinstance(segmentation_result, list) else transcript
                
                # 從檔名和逐字稿內容萃取會議資訊 
                meeting_info = self._extract_meeting_info(processed_transcript, transcript_file)
                
                # 增強提示詞內容與結構
                prompt = f"""
請根據以下會議資訊與逐字稿內容，產生一份完整的結構化會議記錄。

### 固定資訊 (不可更改)
會議編號：{meeting_info["number"] or "無編號"}
會議主題：{meeting_info["topic"] or "市政會議"}
會議日期：{meeting_info["date"]}

### 您的任務
1. 嚴格按照以下格式產出會議記錄：
```markdown
# 會議記錄

會議編號：{meeting_info["number"] or "無編號"} 
會議名稱：{meeting_info["topic"] or "市政會議"}
會議日期：{meeting_info["date"]}

## 與會人員
主席：
出席人員：
列席人員：

## 討論事項
### 一、例行表揚與頒獎
...

### 二、主席致詞重點
...

### 三、專案報告
1. 「你一定要知道的是電器的選擇」(消防局)
   - 統計分析:
   - 主要建議:
   - 改善措施:

### 四、提案討論
1. 案號:
   提案機關:
   案由:
   決議:

## 決議事項
1. ...
2. ...

## 臨時動議與指示事項
...

## 散會時間
...
```

2. 內容要求：
   - 必須按照上述格式排版
   - 準確摘錄會議中的重要決定、指示及共識
   - 清楚列出各項目的討論要點和結論
   - 使用客觀、公正的語氣描述
   - 避免冗長敘述，以重點條列呈現

逐字稿內容：
{processed_transcript}

請按照指定格式提供完整的會議記錄。
"""

                try:
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=300  # 延長超時時間至 300 秒
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("response", "").strip()
                        self.logger.debug(f"[DEBUG] Batch {idx} LLM response:\n{content}")
                        
                        # 檢查生成的內容是否符合格式要求
                        if not content or content.isspace():
                            self.logger.warning(f"[WARNING] 生成的會議記錄為空，使用模板替代")
                            results.append(template)
                        else:
                            results.append(content)
                    else:
                        self.logger.error(f"Ollama API 回應失敗: {response.status_code} {response.text}")
                        results.append(template)
                except requests.exceptions.Timeout:
                    self.logger.error(f"Ollama API 請求超時")
                    results.append(template)
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Ollama API 請求異常: {str(e)}")
                    results.append(template)
                    
            except Exception as e:
                self.logger.error(f"生成會議記錄過程中發生錯誤: {str(e)}")
                results.append(template)
                
        return results

    def _extract_meeting_info(self, transcript: str, transcript_file: str) -> Dict[str, str]:
        """從逐字稿內容和檔名萃取會議資訊"""
        info = {
            "number": "",
            "topic": "",
            "date": "",
            "participants": "",
            "time": ""
        }

        # 1. 從檔名萃取資訊
        if transcript_file:
            try:
                # 匹配「第XXX次市政會議XXX年XX月XX日」格式的檔名
                match = re.search(r'第(\d+)次市政會議(\d+)年(\d+)月(\d+)日', transcript_file)
                if match:
                    number = match.group(1)
                    year = int(match.group(2)) + 1911  # 民國年轉西元年
                    month = match.group(3).zfill(2)
                    day = match.group(4).zfill(2)
                    
                    info["number"] = number
                    info["topic"] = f"第{number}次市政會議"
                    info["date"] = f"{year}年{month}月{day}日"
            except Exception as e:
                self.logger.error(f"解析檔名時發生錯誤: {str(e)}")

        # 2. 從逐字稿內容萃取資訊
        if transcript:
            try:
                # 嘗試找出會議編號和主題
                match = re.search(r'召開台中市政府第(\d+)次市政會議', transcript)
                if match and not info["number"]:
                    number = match.group(1)
                    info["number"] = number
                    info["topic"] = f"第{number}次市政會議"

                # 如果檔名未提供日期，嘗試從內容萃取
                if not info["date"]:
                    date_match = re.search(r'(\d{3})年(\d{1,2})月(\d{1,2})日', transcript)
                    if date_match:
                        year = int(date_match.group(1)) + 1911  # 民國年轉西元年
                        month = date_match.group(2).zfill(2)
                        day = date_match.group(3).zfill(2)
                        info["date"] = f"{year}年{month}月{day}日"

                # 嘗試找出與會人員
                participants_match = re.search(r'各位([\w、，]+)大家好', transcript)
                if participants_match:
                    info["participants"] = participants_match.group(1).replace("、", "、").replace("，", "、")
            except Exception as e:
                self.logger.error(f"解析逐字稿內容時發生錯誤: {str(e)}")

        return info

    def _evaluate_minutes_batch(self, generated_minutes: List[str], reference_minutes: List[str]) -> Dict[str, float]:
        """評估生成的會議記錄品質，回傳指標 dict"""
        scores = {}
        try:
            if self.evaluator:
                for idx, (gen, ref) in enumerate(zip(generated_minutes, reference_minutes)):
                    eval_result = self.evaluator.evaluate(gen, ref)
                    
                    # 首先處理 overall_score
                    if 'overall_score' in eval_result and isinstance(eval_result['overall_score'], (int, float)):
                        if 'overall_score' not in scores:
                            scores['overall_score'] = 0.0
                        scores['overall_score'] += eval_result['overall_score'] / len(generated_minutes)
                    
                    # 然後處理其他分數
                    for metric, value in eval_result.items():
                        if metric == 'overall_score':
                            continue  # 已經處理過
                        elif isinstance(value, (int, float)):
                            # 直接是數值的分數
                            if metric not in scores:
                                scores[metric] = 0.0
                            scores[metric] += value / len(generated_minutes)
                        elif isinstance(value, dict) and 'score' in value:
                            # 包含 score 鍵的字典
                            score_val = value['score']
                            if isinstance(score_val, (int, float)):
                                metric_name = f"{metric}_score"
                                if metric_name not in scores:
                                    scores[metric_name] = 0.0
                                scores[metric_name] += score_val / len(generated_minutes)
                        elif metric == 'categories' and isinstance(value, dict):
                            # 處理categories結構
                            for cat_name, cat_data in value.items():
                                if isinstance(cat_data, dict) and 'score' in cat_data:
                                    cat_score = cat_data['score']
                                    if isinstance(cat_score, (int, float)):
                                        metric_name = f"{cat_name}_score"
                                        if metric_name not in scores:
                                            scores[metric_name] = 0.0
                                        scores[metric_name] += cat_score / len(generated_minutes)
            else:
                self.logger.warning("評估器未啟用，無法評估生成品質")
                scores = {"overall_score": 0.5}  # 預設分數
        except Exception as e:
            self.logger.error(f"評估過程中發生錯誤: {str(e)}")
            scores = {"overall_score": 0.0}  # 錯誤時的預設分數
        return scores

    def _save_best_minutes(self, minutes: str, metrics: Dict[str, float], score: float) -> None:
        """儲存最佳的會議記錄 (同時存 json 與 txt)"""
        self.logger.info(f"儲存最佳會議記錄，綜合分數: {score:.4f}")
        topic = metrics.get("topic", "無主題")
        date = metrics.get("date", "無日期")
        number = metrics.get("number", "無編號")
        base_name = f"{topic}_{date}_{number}_優化後".replace("/", "_").replace(" ", "_")
        json_path = self.output_dir / f"{base_name}.json"
        txt_path = self.output_dir / f"{base_name}.txt"

        # 檢查檔案是否已存在，若存在則改名
        if json_path.exists() or txt_path.exists():
            counter = 1
            while (self.output_dir / f"{base_name}_{counter}.json").exists() or (self.output_dir / f"{base_name}_{counter}.txt").exists():
                counter += 1
            json_path = self.output_dir / f"{base_name}_{counter}.json"
            txt_path = self.output_dir / f"{base_name}_{counter}.txt"

        # 儲存 json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "minutes": minutes,
                "metrics": metrics,
                "score": score
            }, f, ensure_ascii=False, indent=4)
        # 儲存 txt（只存 minutes 純文字）
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(minutes)
        self.logger.info(f"最佳會議記錄已儲存至: {json_path} 及 {txt_path}")
    
    def _save_best_template(self, template: str, metrics: Dict[str, float], score: float) -> None:
        """儲存最佳的模板"""
        self.logger.info(f"儲存最佳模板，綜合分數: {score:.4f}")
        # 儲存格式：模板_會議主題_日期_會議編號.json
        topic = metrics.get("topic", "無主題")
        date = metrics.get("date", "無日期")
        number = metrics.get("number", "無編號")
        file_name = f"模板_{topic}_{date}_{number}.json".replace("/", "_").replace(" ", "_")
        file_path = self.output_dir / file_name
        
        # 檢查檔案是否已存在，若存在則改名
        if file_path.exists():
            base_name = file_path.stem
            extension = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = self.output_dir / f"{base_name}_{counter}{extension}"
                counter += 1
        
        # 儲存檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "template": template,
                "metrics": metrics,
                "score": score
            }, f, ensure_ascii=False, indent=4)
        
        self.logger.info(f"最佳模板已儲存至: {file_path}")
    
    def _refine_template_and_strategy_with_llm(self, transcript: str, best_minutes: str, reference: str) -> tuple:
        """
        呼叫 Gemma3:12B，根據逐字稿、最佳 minutes、reference，自動優化 template 與策略
        回傳 (new_template, new_strategy_dict)
        """
        import requests
        prompt = f"""
你是一位會議記錄優化專家。請根據下列三份資料：
1. 逐字稿：\n{transcript}\n
2. 目前最佳 minutes：\n{best_minutes}\n
3. 標準 reference 會議記錄：\n{reference}\n
請分析最佳 minutes 與 reference 的差異，並針對 minutes 結構、格式、重點提取、條列方式等，提出具體改進建議。
請直接輸出：
A. 新的 minutes 產生模板（以 {{topic}}、{{date}}、{{participants}} 等變數標示）
B. 策略參數建議（如哪些重點要強化、哪些格式要調整，請用 JSON 格式）

請用如下格式回覆：
---TEMPLATE---\n(新 minutes template)\n---STRATEGY---\n(策略 JSON)\n---END---
"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:12b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300
            )
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                # 解析 LLM 回傳格式
                template = None
                strategy = None
                if "---TEMPLATE---" in content and "---STRATEGY---" in content:
                    t1 = content.find("---TEMPLATE---") + len("---TEMPLATE---")
                    t2 = content.find("---STRATEGY---")
                    s1 = t2 + len("---STRATEGY---")
                    s2 = content.find("---END---") if "---END---" in content else len(content)
                    template = content[t1:t2].strip()
                    strategy_str = content[s1:s2].strip()
                    try:
                        import json as _json
                        strategy = _json.loads(strategy_str)
                    except Exception:
                        strategy = {}
                return template, strategy
            else:
                self.logger.error(f"Gemma3:12B API 回應失敗: {response.status_code} {response.text}")
        except Exception as e:
            self.logger.error(f"呼叫 Gemma3:12B refine template/strategy 失敗: {str(e)}")
        return None, None

def process_transcript(
    optimizer: 'MeetingOptimizer',
    transcript_path: Path,
    reference_dir: Optional[Path] = None,
    max_iterations: int = 2,
    batch_size: int = 3,
    **kwargs
):
    """
    處理單一逐字稿，尋找對應 reference，並進行 minutes 優化
    """
    if reference_dir is None:
        reference_dir = transcript_path.parent.parent / "reference"
    transcript_file = transcript_path.name
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # 嘗試自動尋找 reference 檔案
    base_name = Path(transcript_file).stem
    possible_exts = [".txt", ".md", ".json"]
    ref_file = None
    for ext in possible_exts:
        candidate = reference_dir / (base_name + ext)
        if candidate.exists():
            ref_file = candidate
            break

    if not ref_file:
        print(f"[警告] 找不到對應的 reference 檔案於 {reference_dir}，將僅以逐字稿產生 minutes。")
        reference = transcript  # 直接用逐字稿作為 reference，允許產生 minutes
    else:
        with open(ref_file, "r", encoding="utf-8") as f:
            reference = f.read()

    matched_data = [{
        "transcript": transcript,
        "transcript_file": transcript_file,
        "reference": reference,
        "reference_file": str(ref_file) if ref_file else ""
    }]

    # 呼叫 optimize
    optimizer.optimize(
        matched_data,
        max_iterations=max_iterations,
        batch_size=batch_size
    )
