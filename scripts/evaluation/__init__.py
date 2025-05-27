"""
會議記錄評估模組

提供多指標評估功能，包括語義相似度、內容覆蓋度和結構化程度等。
"""

from .config import EvaluationConfig, MetricConfig, MetricCategory
from .evaluator import MeetingEvaluator

__all__ = [
    'EvaluationConfig',
    'MetricConfig',
    'MetricCategory',
    'MeetingEvaluator'
]
