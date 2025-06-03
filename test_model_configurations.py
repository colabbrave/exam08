#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
會議記錄優化系統 - 模型配置測試與評估工具
基於 MODEL_OPTIMIZATION_ANALYSIS.md 的建議方案進行測試
"""

import os
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """模型配置資料結構"""
    name: str
    generation_model: str
    optimization_model: str
    embedding_model: str = "nomic-embed-text:latest"
    description: str = ""
    expected_improvements: Optional[Dict[str, Any]] = None  # 改為 Optional 和 Any 類型

class ModelConfigurationTester:
    """模型配置測試器"""
    
    def __init__(self, output_dir: str = "model_config_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 設置日誌
        self.logger = self._setup_logger()
        
        # 定義測試配置
        self.test_configs = self._define_test_configurations()
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌"""
        logger = logging.getLogger("ModelConfigTester")
        logger.setLevel(logging.INFO)
        
        if logger.hasHandlers():
            logger.handlers.clear()
            
        # 文件處理器
        log_file = self.output_dir / "model_config_test.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式設置
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _define_test_configurations(self) -> List[ModelConfig]:
        """定義測試模型配置
        
        基於 MODEL_OPTIMIZATION_ANALYSIS.md 中的模型規格比較表和三個優化方案
        """
        return [
            # 方案一：雙Gemma架構（推薦）⭐⭐⭐⭐⭐
            ModelConfig(
                name="dual_gemma_recommended",
                generation_model="gemma3:12b",
                optimization_model="gemma3:12b",
                embedding_model="nomic-embed-text:latest",
                description="雙Gemma架構 - 12B參數，128K上下文，統一強推理能力，量化感知訓練",
                expected_improvements={
                    "quality_improvement": 0.15,  # +15%
                    "stability_sigma": 0.05,      # σ<0.05
                    "avg_iterations": 25,          # 25輪
                    "processing_time": 120,        # 120分鐘
                    "context_length": 128000,      # 128K上下文
                    "model_rating": 5,             # ⭐⭐⭐⭐⭐
                    "technical_advantages": ["強推理能力", "長上下文", "記憶體效率", "多模態支持"]
                }
            ),
            
            # 方案二：混合最佳化架構 ⭐⭐⭐⭐
            ModelConfig(
                name="hybrid_llama_gemma",
                generation_model="llama3.1:8b",
                optimization_model="gemma3:12b",
                embedding_model="nomic-embed-text:latest",
                description="混合架構 - Llama3.1(128K上下文+工具使用) + Gemma3:12b(強推理)",
                expected_improvements={
                    "quality_improvement": 0.12,  # +12%
                    "stability_sigma": 0.08,      # σ<0.08
                    "avg_iterations": 30,          # 30輪
                    "processing_time": 135,        # 135分鐘
                    "context_length": 128000,      # 128K上下文
                    "model_rating": 4,             # ⭐⭐⭐⭐
                    "technical_advantages": ["超長上下文", "工具使用能力", "多語言支持", "強推理優化"]
                }
            ),
            
            # 方案三：繁中優化架構 ⭐⭐⭐⭐
            ModelConfig(
                name="taide_optimized_chinese",
                generation_model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                optimization_model="gemma3:12b",
                embedding_model="nomic-embed-text:latest",
                description="繁中優化架構 - TAIDE繁體中文特優 + Gemma3:12b推理 + 升級embedding",
                expected_improvements={
                    "quality_improvement": 0.08,  # +8%
                    "stability_sigma": 0.12,      # σ<0.12
                    "avg_iterations": 35,          # 35輪
                    "processing_time": 140,        # 140分鐘
                    "context_length": 8192,        # 8K上下文
                    "model_rating": 4,             # ⭐⭐⭐⭐
                    "technical_advantages": ["繁體中文特優", "中翻英優異", "最小變更風險", "穩定基礎"]
                }
            ),
            
            # 輕量化方案：Gemma3:4b架構 ⭐⭐⭐
            ModelConfig(
                name="lightweight_gemma",
                generation_model="gemma3:4b",
                optimization_model="gemma3:12b",
                embedding_model="nomic-embed-text:latest",
                description="輕量架構 - Gemma3:4b生成 + Gemma3:12b優化，資源效率高",
                expected_improvements={
                    "quality_improvement": 0.06,  # +6%
                    "stability_sigma": 0.10,      # σ<0.10
                    "avg_iterations": 40,          # 40輪
                    "processing_time": 100,        # 100分鐘
                    "context_length": 128000,      # 128K上下文
                    "model_rating": 3,             # ⭐⭐⭐
                    "technical_advantages": ["輕量設計", "資源效率", "快速處理", "128K上下文"]
                }
            ),
            
            # 基準線：當前系統配置
            ModelConfig(
                name="current_baseline",
                generation_model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest",
                optimization_model="gemma3:12b",
                embedding_model="current",  # 當前embedding系統
                description="當前系統配置 - 基準線測試（TAIDE + Gemma3:12b + 舊embedding）",
                expected_improvements={
                    "quality_improvement": 0.00,  # 基準線
                    "stability_sigma": 0.2078,    # 當前σ
                    "avg_iterations": 63,          # 當前平均
                    "processing_time": 145.8,      # 當前時間
                    "context_length": 8192,        # 8K上下文
                    "model_rating": 3,             # 當前基準
                    "technical_advantages": ["已驗證穩定", "繁體中文優勢", "現有配置"]
                }
            )
        ]
    
    def check_model_availability(self, model_name: str) -> bool:
        """檢查模型是否可用"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                available_models = result.stdout
                return model_name in available_models
            else:
                self.logger.error(f"檢查模型時出錯: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"檢查模型 {model_name} 可用性時出錯: {e}")
            return False
    
    def download_model_if_needed(self, model_name: str) -> bool:
        """如果需要，下載模型"""
        if self.check_model_availability(model_name):
            self.logger.info(f"模型 {model_name} 已存在")
            return True
            
        self.logger.info(f"正在下載模型 {model_name}...")
        try:
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=1800  # 30分鐘超時
            )
            
            if result.returncode == 0:
                self.logger.info(f"模型 {model_name} 下載成功")
                return True
            else:
                self.logger.error(f"模型 {model_name} 下載失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"模型 {model_name} 下載超時")
            return False
        except Exception as e:
            self.logger.error(f"下載模型 {model_name} 時出錯: {e}")
            return False
    
    def run_baseline_test(self, config: ModelConfig, max_iterations: int = 10) -> Dict[str, Any]:
        """執行基準測試"""
        self.logger.info(f"開始測試配置: {config.name}")
        self.logger.info(f"描述: {config.description}")
        
        # 檢查並下載必要模型
        models_to_check = [config.generation_model, config.optimization_model]
        
        for model_name in models_to_check:
            if model_name == "current":  # 跳過當前embedding標記
                continue
                
            if not self.download_model_if_needed(model_name):
                self.logger.error(f"無法獲取模型 {model_name}，跳過此配置測試")
                return {
                    "config_name": config.name,
                    "status": "failed",
                    "error": f"模型 {model_name} 不可用",
                    "timestamp": datetime.now().isoformat()
                }
        
        # 執行優化測試
        test_start_time = time.time()
        
        try:
            # 構建測試命令
            cmd = [
                "python", "scripts/iterative_optimizer.py",
                "--transcript-dir", "data/transcript",
                "--model", config.generation_model,
                "--optimization-model", config.optimization_model,
                "--max-iterations", str(max_iterations),
                "--quality-threshold", "0.8"
            ]
            
            self.logger.info(f"執行測試命令: {' '.join(cmd)}")
            
            # 執行測試
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小時超時
            )
            
            test_duration = time.time() - test_start_time
            
            if result.returncode == 0:
                self.logger.info(f"配置 {config.name} 測試完成，耗時 {test_duration:.2f} 秒")
                
                # 解析測試結果
                test_results = self._parse_test_results(config.name, result.stdout)
                test_results.update({
                    "config_name": config.name,
                    "status": "success",
                    "test_duration": test_duration,
                    "timestamp": datetime.now().isoformat(),
                    "expected_improvements": config.expected_improvements
                })
                
                return test_results
            else:
                self.logger.error(f"配置 {config.name} 測試失敗: {result.stderr}")
                return {
                    "config_name": config.name,
                    "status": "failed",
                    "error": result.stderr,
                    "test_duration": test_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"配置 {config.name} 測試超時")
            return {
                "config_name": config.name,
                "status": "timeout",
                "test_duration": time.time() - test_start_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"測試配置 {config.name} 時出錯: {e}")
            return {
                "config_name": config.name,
                "status": "error",
                "error": str(e),
                "test_duration": time.time() - test_start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_test_results(self, config_name: str, stdout: str) -> Dict[str, Any]:
        """解析測試結果"""
        # 這裡實現結果解析邏輯
        # 暫時返回基本資訊
        return {
            "parsing_status": "basic",
            "stdout_length": len(stdout),
            "note": "詳細結果解析待實現"
        }
    
    def run_comprehensive_test(self, max_iterations: int = 10) -> Dict[str, Any]:
        """執行全面配置測試"""
        self.logger.info("開始執行全面模型配置測試")
        self.logger.info(f"測試 {len(self.test_configs)} 個配置")
        
        all_results = {
            "test_start_time": datetime.now().isoformat(),
            "test_parameters": {
                "max_iterations": max_iterations,
                "configs_tested": len(self.test_configs)
            },
            "config_results": {},
            "summary": {}
        }
        
        # 逐一測試每個配置
        for config in self.test_configs:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"測試配置: {config.name}")
            self.logger.info(f"{'='*60}")
            
            config_result = self.run_baseline_test(config, max_iterations)
            all_results["config_results"][config.name] = config_result
            
            # 簡短休息，避免系統過載
            time.sleep(10)
        
        # 生成測試總結
        all_results["summary"] = self._generate_test_summary(all_results["config_results"])
        all_results["test_end_time"] = datetime.now().isoformat()
        
        # 保存結果
        results_file = self.output_dir / f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"測試完成，結果已保存至: {results_file}")
        return all_results
    
    def _generate_test_summary(self, config_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成測試總結"""
        summary = {
            "total_configs": len(config_results),
            "successful_tests": 0,
            "failed_tests": 0,
            "timeout_tests": 0,
            "recommendations": []
        }
        
        for config_name, result in config_results.items():
            status = result.get("status", "unknown")
            if status == "success":
                summary["successful_tests"] += 1
            elif status == "failed" or status == "error":
                summary["failed_tests"] += 1
            elif status == "timeout":
                summary["timeout_tests"] += 1
        
        # 生成建議
        if summary["successful_tests"] > 0:
            summary["recommendations"].append("至少有一個配置測試成功，可以進行下一步分析")
        
        if summary["failed_tests"] > 0:
            summary["recommendations"].append("部分配置測試失敗，建議檢查模型可用性和系統資源")
        
        return summary

    def generate_model_specs_comparison(self) -> Dict[str, Any]:
        """生成模型規格比較報告"""
        self.logger.info("生成模型規格比較報告")
        
        comparison_data = {
            "report_timestamp": datetime.now().isoformat(),
            "model_specifications": {},
            "ranking_analysis": {},
            "recommendations": {}
        }
        
        # 為每個配置生成規格分析
        for config in self.test_configs:
            specs = {
                "configuration_name": config.name,
                "generation_model": config.generation_model,
                "optimization_model": config.optimization_model,
                "embedding_model": config.embedding_model,
                "description": config.description,
                "expected_improvements": config.expected_improvements or {},
                "model_rating": config.expected_improvements.get("model_rating", 0) if config.expected_improvements else 0,
                "context_length": config.expected_improvements.get("context_length", 0) if config.expected_improvements else 0,
                "technical_advantages": config.expected_improvements.get("technical_advantages", []) if config.expected_improvements else []
            }
            comparison_data["model_specifications"][config.name] = specs
        
        # 生成排名分析
        rankings = sorted(
            self.test_configs,
            key=lambda x: x.expected_improvements.get("quality_improvement", 0) if x.expected_improvements else 0,
            reverse=True
        )
        
        comparison_data["ranking_analysis"] = {
            "by_quality_improvement": [
                {
                    "rank": i+1,
                    "config_name": config.name,
                    "expected_improvement": config.expected_improvements.get("quality_improvement", 0) if config.expected_improvements else 0,
                    "rating": config.expected_improvements.get("model_rating", 0) if config.expected_improvements else 0
                }
                for i, config in enumerate(rankings)
            ],
            "by_stability": sorted([
                {
                    "config_name": config.name,
                    "expected_sigma": config.expected_improvements.get("stability_sigma", 1.0) if config.expected_improvements else 1.0,
                    "stability_score": 1.0 / (config.expected_improvements.get("stability_sigma", 1.0) + 0.01) if config.expected_improvements else 0.01
                }
                for config in self.test_configs
            ], key=lambda x: x["stability_score"], reverse=True)
        }
        
        # 生成建議
        best_config = rankings[0] if rankings else None
        comparison_data["recommendations"] = {
            "top_recommendation": best_config.name if best_config else "無法確定",
            "reasoning": f"基於模型規格分析，{best_config.name}具有最高的品質改善潛力" if best_config else "需要更多數據",
            "implementation_priority": [
                f"立即測試: {rankings[0].name}" if len(rankings) > 0 else "",
                f"次要選擇: {rankings[1].name}" if len(rankings) > 1 else "",
                f"備用方案: {rankings[2].name}" if len(rankings) > 2 else ""
            ],
            "risk_assessment": {
                "high_performance": [config.name for config in self.test_configs if config.expected_improvements and config.expected_improvements.get("model_rating", 0) >= 5],
                "moderate_risk": [config.name for config in self.test_configs if config.expected_improvements and config.expected_improvements.get("model_rating", 0) == 4],
                "conservative_choice": [config.name for config in self.test_configs if config.expected_improvements and config.expected_improvements.get("model_rating", 0) <= 3]
            }
        }
        
        # 保存比較報告
        report_file = self.output_dir / f"model_specs_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"模型規格比較報告已生成: {report_file}")
        return comparison_data

    def run_quick_validation_test(self, config_name: str) -> Dict[str, Any]:
        """執行快速驗證測試（僅檢查模型可用性和基本功能）"""
        config = next((c for c in self.test_configs if c.name == config_name), None)
        if not config:
            return {"error": f"找不到配置: {config_name}"}
        
        self.logger.info(f"執行快速驗證測試: {config_name}")
        
        validation_result = {
            "config_name": config_name,
            "timestamp": datetime.now().isoformat(),
            "model_availability": {},
            "basic_functionality": {},
            "validation_status": "unknown"
        }
        
        # 檢查模型可用性
        models_to_check = [config.generation_model, config.optimization_model]
        if config.embedding_model != "current":
            models_to_check.append(config.embedding_model)
        
        all_available = True
        for model in models_to_check:
            available = self.check_model_availability(model)
            validation_result["model_availability"][model] = available
            if not available:
                all_available = False
                self.logger.warning(f"模型 {model} 不可用")
        
        if all_available:
            validation_result["validation_status"] = "models_ready"
            self.logger.info(f"配置 {config_name} 的所有模型都可用")
        else:
            validation_result["validation_status"] = "models_missing"
            self.logger.error(f"配置 {config_name} 缺少必要模型")
        
        return validation_result

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="會議記錄優化系統 - 模型配置測試工具")
    parser.add_argument("--mode", choices=["specs", "validate", "quick", "full"], default="specs",
                       help="測試模式: specs=生成規格比較, validate=驗證模型可用性, quick=快速測試, full=完整測試")
    parser.add_argument("--config", type=str, help="指定測試的配置名稱")
    parser.add_argument("--max-iterations", type=int, default=5, help="最大疊代次數（用於quick/full模式）")
    parser.add_argument("--output-dir", type=str, default="model_config_tests", help="輸出目錄")
    
    args = parser.parse_args()
    
    # 創建測試器
    tester = ModelConfigurationTester(output_dir=args.output_dir)
    
    try:
        if args.mode == "specs":
            # 生成模型規格比較報告
            print("🔍 生成模型規格比較報告...")
            comparison = tester.generate_model_specs_comparison()
            print(f"✅ 規格比較報告已生成，共分析 {len(comparison['model_specifications'])} 個配置")
            
            # 顯示推薦配置
            if comparison["recommendations"]["top_recommendation"] != "無法確定":
                print(f"🚀 推薦配置: {comparison['recommendations']['top_recommendation']}")
                print(f"📝 推薦理由: {comparison['recommendations']['reasoning']}")
                
                # 顯示實施優先級
                print("\n📋 實施優先級:")
                for priority in comparison["recommendations"]["implementation_priority"]:
                    if priority:  # 只顯示非空的優先級
                        print(f"   • {priority}")
        
        elif args.mode == "validate":
            # 驗證所有配置的模型可用性
            print("🔧 驗證模型可用性...")
            validation_results = {}
            
            configs_to_test = [args.config] if args.config else [c.name for c in tester.test_configs]
            
            for config_name in configs_to_test:
                print(f"\n📋 驗證配置: {config_name}")
                result = tester.run_quick_validation_test(config_name)
                validation_results[config_name] = result
                
                status = result.get("validation_status", "unknown")
                if status == "models_ready":
                    print(f"✅ {config_name}: 所有模型可用")
                else:
                    print(f"❌ {config_name}: 缺少必要模型")
                    for model, available in result.get("model_availability", {}).items():
                        if not available:
                            print(f"   ⚠️  {model} 不可用")
            
            # 保存驗證結果
            validation_file = Path(args.output_dir) / f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2, ensure_ascii=False)
            print(f"\n📊 驗證結果已保存: {validation_file}")
        
        elif args.mode == "quick":
            # 快速基準測試
            print(f"⚡ 執行快速基準測試（{args.max_iterations}次疊代）...")
            
            if args.config:
                config = next((c for c in tester.test_configs if c.name == args.config), None)
                if config:
                    result = tester.run_baseline_test(config, max_iterations=args.max_iterations)
                    print(f"✅ 配置 {args.config} 測試完成")
                    print(f"📊 狀態: {result.get('status', 'unknown')}")
                else:
                    print(f"❌ 找不到配置: {args.config}")
            else:
                print("❌ 快速測試模式需要指定 --config 參數")
                print("💡 可用配置:")
                for config in tester.test_configs:
                    print(f"   • {config.name}: {config.description}")
        
        elif args.mode == "full":
            # 完整測試
            print(f"🚀 執行完整模型配置測試（{args.max_iterations}次疊代）...")
            results = tester.run_comprehensive_test(max_iterations=args.max_iterations)
            
            print("\n📊 測試總結:")
            summary = results.get("summary", {})
            print(f"   總配置數: {summary.get('total_configs', 0)}")
            print(f"   成功測試: {summary.get('successful_tests', 0)}")
            print(f"   失敗測試: {summary.get('failed_tests', 0)}")
            print(f"   超時測試: {summary.get('timeout_tests', 0)}")
            
            # 顯示推薦
            recommendations = summary.get("recommendations", [])
            if recommendations:
                print("\n💡 系統建議:")
                for rec in recommendations[:3]:  # 顯示前三個建議
                    print(f"   • {rec}")
    
    except KeyboardInterrupt:
        print("\n🛑 用戶中斷測試")
    except Exception as e:
        print(f"❌ 測試過程中出錯: {e}")
        tester.logger.error(f"測試失敗: {e}")
    
    print("\n🏁 測試程式結束")

if __name__ == "__main__":
    main()
