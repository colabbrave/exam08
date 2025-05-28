"""
評估系統配置模組

定義評估指標的配置和權重
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class MetricConfig:
    """單個指標的配置"""
    name: str
    enabled: bool = True
    weight: float = 1.0
    description: str = ""
    higher_is_better: bool = True
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "weight": self.weight,
            "description": self.description,
            "higher_is_better": self.higher_is_better
        }

@dataclass
class MetricCategory:
    """指標類別配置"""
    name: str
    metrics: Dict[str, MetricConfig] = field(default_factory=dict)
    enabled: bool = True
    weight: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "weight": self.weight,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()}
        }
    
    def add_metric(self, metric: MetricConfig):
        self.metrics[metric.name] = metric

class EvaluationConfig:
    """評估系統配置"""
    
    def __init__(self):
        self.categories: Dict[str, MetricCategory] = {}
        self._initialize_default_config()
    
    def _initialize_default_config(self):
        """初始化默認配置"""
        # 1. 語義相似度
        semantic = MetricCategory("semantic_similarity", weight=0.3)
        semantic.add_metric(MetricConfig(
            name="bertscore_f1",
            weight=1.0,
            description="BERTScore F1 分數，衡量語義相似度"
        ))
        self.add_category(semantic)
        
        # 2. 內容覆蓋度
        coverage = MetricCategory("content_coverage", weight=0.3)
        coverage.add_metric(MetricConfig(
            name="rouge1",
            weight=0.3,
            description="ROUGE-1 F1 分數，衡量 unigram 層面的覆蓋度"
        ))
        coverage.add_metric(MetricConfig(
            name="rouge2",
            weight=0.4,
            description="ROUGE-2 F1 分數，衡量 bigram 層面的覆蓋度"
        ))
        coverage.add_metric(MetricConfig(
            name="rougeL",
            weight=0.3,
            description="ROUGE-L F1 分數，衡量最長公共子序列"
        ))
        self.add_category(coverage)
        
        # 3. 結構化程度
        structure = MetricCategory("structure_quality", weight=0.2)
        structure.add_metric(MetricConfig(
            name="section_heading_quality",
            weight=0.4,
            description="章節標題質量"
        ))
        structure.add_metric(MetricConfig(
            name="paragraph_structure",
            weight=0.3,
            description="段落結構質量"
        ))
        structure.add_metric(MetricConfig(
            name="list_usage",
            weight=0.3,
            description="列表使用適當性"
        ))
        self.add_category(structure)
        
        # 4. 穩定性
        stability = MetricCategory("stability", weight=0.2)
        stability.add_metric(MetricConfig(
            name="format_consistency",
            weight=0.4,
            description="格式一致性（多次生成的格式相似度）"
        ))
        stability.add_metric(MetricConfig(
            name="length_variation",
            weight=0.3,
            description="長度穩定性（長度變異係數）",
            higher_is_better=False
        ))
        stability.add_metric(MetricConfig(
            name="key_entities_consistency",
            weight=0.3,
            description="關鍵實體一致性"
        ))
        self.add_category(stability)
    
    def add_category(self, category: MetricCategory):
        """添加指標類別"""
        self.categories[category.name] = category
    
    def get_metric(self, category_name: str, metric_name: str) -> Optional[MetricConfig]:
        """獲取指定指標配置"""
        if category_name in self.categories:
            return self.categories[category_name].metrics.get(metric_name)
        return None
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "categories": {
                name: category.to_dict() 
                for name, category in self.categories.items()
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'EvaluationConfig':
        """從字典加載配置"""
        config = cls()
        for cat_name, cat_data in config_dict.get("categories", {}).items():
            category = MetricCategory(
                name=cat_data.get("name", cat_name),
                enabled=cat_data.get("enabled", True),
                weight=cat_data.get("weight", 1.0)
            )
            for metric_name, metric_data in cat_data.get("metrics", {}).items():
                category.add_metric(MetricConfig(
                    name=metric_data.get("name", metric_name),
                    enabled=metric_data.get("enabled", True),
                    weight=metric_data.get("weight", 1.0),
                    description=metric_data.get("description", ""),
                    higher_is_better=metric_data.get("higher_is_better", True)
                ))
            config.categories[cat_name] = category
        return config
