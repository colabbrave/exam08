#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語意分段配置管理模組
"""

import os
import configparser
from typing import Dict, Any
from pathlib import Path


from typing import Optional

class SemanticConfig:
    """語意分段配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路徑，如果為None則使用默認路徑
        """
        if config_file is None:
            # 使用默認配置文件路徑
            script_dir = Path(__file__).parent.parent
            self.config_file = str(script_dir / "config" / "semantic_config.ini")
        else:
            self.config_file = config_file
        
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """載入配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            # 如果配置文件不存在，使用默認配置
            self._create_default_config()
    
    def _create_default_config(self):
        """創建默認配置"""
        self.config['models'] = {
            'splitter_model': 'gemma3:12b',
            'generator_model': 'cwchang/llama3-taide-lx-8b-chat-alpha1:latest',
            'ollama_url': 'http://localhost:11434/api/generate'
        }
        
        self.config['segmentation'] = {
            'max_segment_length': '4000',
            'overlap_length': '200',
            'enable_ai_optimization': 'true'
        }
        
        self.config['quality'] = {
            'quality_threshold': '6.0',
            'enable_quality_check': 'true',
            'max_retry_attempts': '2',
            'excellent_threshold': '8.5',
            'good_threshold': '7.0',
            'acceptable_threshold': '5.5',
            'poor_threshold': '3.0'
        }
        
        self.config['processing'] = {
            'api_timeout': '300',
            'splitter_temperature': '0.3',
            'generator_temperature': '0.2',
            'merge_temperature': '0.1',
            'file_patterns': '*.txt,*.md,*.docx'
        }
        
        self.config['output'] = {
            'default_output_dir': 'output',
            'save_intermediate_results': 'true',
            'generate_detailed_report': 'true'
        }
        
        self.config['logging'] = {
            'log_level': 'INFO',
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        獲取配置值
        
        Args:
            section: 配置節名
            key: 配置鍵名
            fallback: 默認值
            
        Returns:
            配置值
        """
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """獲取整數配置值"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """獲取浮點數配置值"""
        return self.config.getfloat(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """獲取布爾配置值"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def get_models_config(self) -> Dict[str, str]:
        """獲取模型配置"""
        return {
            'splitter_model': self.get('models', 'splitter_model', 'gemma3:12b'),
            'generator_model': self.get('models', 'generator_model', 
                                     'cwchang/llama3-taide-lx-8b-chat-alpha1:latest'),
            'ollama_url': self.get('models', 'ollama_url', 'http://localhost:11434/api/generate')
        }
    
    def get_segmentation_config(self) -> Dict[str, Any]:
        """獲取分段配置"""
        return {
            'max_segment_length': self.getint('segmentation', 'max_segment_length', 4000),
            'overlap_length': self.getint('segmentation', 'overlap_length', 200),
            'enable_ai_optimization': self.getboolean('segmentation', 'enable_ai_optimization', True)
        }
    
    def get_quality_config(self) -> Dict[str, Any]:
        """獲取品質配置"""
        return {
            'quality_threshold': self.getfloat('quality', 'quality_threshold', 6.0),
            'enable_quality_check': self.getboolean('quality', 'enable_quality_check', True),
            'max_retry_attempts': self.getint('quality', 'max_retry_attempts', 2),
            'thresholds': {
                'excellent': self.getfloat('quality', 'excellent_threshold', 8.5),
                'good': self.getfloat('quality', 'good_threshold', 7.0),
                'acceptable': self.getfloat('quality', 'acceptable_threshold', 5.5),
                'poor': self.getfloat('quality', 'poor_threshold', 3.0)
            }
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """獲取處理配置"""
        file_patterns = self.get('processing', 'file_patterns', '*.txt,*.md').split(',')
        return {
            'api_timeout': self.getint('processing', 'api_timeout', 300),
            'temperatures': {
                'splitter': self.getfloat('processing', 'splitter_temperature', 0.3),
                'generator': self.getfloat('processing', 'generator_temperature', 0.2),
                'merge': self.getfloat('processing', 'merge_temperature', 0.1)
            },
            'file_patterns': [pattern.strip() for pattern in file_patterns]
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """獲取輸出配置"""
        return {
            'default_output_dir': self.get('output', 'default_output_dir', 'output'),
            'save_intermediate_results': self.getboolean('output', 'save_intermediate_results', True),
            'generate_detailed_report': self.getboolean('output', 'generate_detailed_report', True)
        }
    
    def get_logging_config(self) -> Dict[str, str]:
        """獲取日誌配置"""
        return {
            'log_level': self.get('logging', 'log_level', 'INFO'),
            'log_format': self.get('logging', 'log_format', 
                                 '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }
    
    def save_config(self, config_file: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路徑，如果為None則保存到當前配置文件
        """
        if config_file is None:
            config_file = self.config_file
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def update_config(self, section: str, key: str, value: Any):
        """
        更新配置值
        
        Args:
            section: 配置節名
            key: 配置鍵名
            value: 新值
        """
        if section not in self.config:
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
    
    def get_all_config(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有配置"""
        return {
            'models': self.get_models_config(),
            'segmentation': self.get_segmentation_config(),
            'quality': self.get_quality_config(),
            'processing': self.get_processing_config(),
            'output': self.get_output_config(),
            'logging': self.get_logging_config()
        }


def main():
    """測試配置管理功能"""
    config = SemanticConfig()
    
    print("=== 語意分段配置 ===")
    
    all_config = config.get_all_config()
    
    for section_name, section_config in all_config.items():
        print(f"\n[{section_name}]")
        for key, value in section_config.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
