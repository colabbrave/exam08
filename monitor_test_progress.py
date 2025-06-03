#!/usr/bin/env python3
"""
實時測試進度監控器
監控模型配置測試的進度並提供狀態更新
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
import glob

class TestProgressMonitor:
    def __init__(self, output_dir="model_config_tests"):
        self.output_dir = Path(output_dir)
        self.start_time = datetime.now()
        
    def check_test_progress(self):
        """檢查測試進度"""
        print(f"🔍 測試進度監控 - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # 檢查日誌文件
        log_files = list(self.output_dir.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"📋 最新日誌: {latest_log.name}")
            self._check_log_progress(latest_log)
        
        # 檢查結果文件
        result_files = list(self.output_dir.glob("*results*.json"))
        if result_files:
            print(f"📊 結果文件: {len(result_files)} 個")
            for file in result_files:
                print(f"   - {file.name}")
        
        # 檢查優化結果
        results_dir = Path("results/optimized")
        if results_dir.exists():
            recent_files = []
            cutoff_time = time.time() - 3600  # 1小時內的文件
            for file in results_dir.glob("*.json"):
                if file.stat().st_mtime > cutoff_time:
                    recent_files.append(file)
            
            if recent_files:
                print(f"🎯 最近的優化結果: {len(recent_files)} 個")
                for file in sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   - {file.name} ({mtime.strftime('%H:%M:%S')})")
    
    def _check_log_progress(self, log_file):
        """檢查日誌文件中的進度"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找最近的進度信息
            recent_lines = lines[-20:]  # 最後20行
            
            config_info = []
            status_info = []
            
            for line in recent_lines:
                line = line.strip()
                if "開始測試配置:" in line:
                    config_info.append(line)
                elif "測試完成" in line or "執行測試命令" in line:
                    status_info.append(line)
            
            if config_info:
                print(f"🔄 當前配置: {config_info[-1].split(':')[-1].strip()}")
            
            if status_info:
                print(f"📈 最新狀態: {status_info[-1].split(']')[-1].strip() if ']' in status_info[-1] else status_info[-1]}")
                
        except Exception as e:
            print(f"⚠️  讀取日誌失敗: {e}")
    
    def get_summary_stats(self):
        """獲取測試統計摘要"""
        elapsed = datetime.now() - self.start_time
        print(f"\n📈 測試統計摘要")
        print(f"運行時間: {elapsed}")
        
        # 統計文件數量
        total_files = len(list(Path("results").rglob("*.json")))
        recent_files = 0
        cutoff_time = time.time() - 3600
        
        for file in Path("results").rglob("*.json"):
            if file.stat().st_mtime > cutoff_time:
                recent_files += 1
        
        print(f"總結果文件: {total_files}")
        print(f"最近1小時: {recent_files}")

def main():
    monitor = TestProgressMonitor()
    
    try:
        while True:
            monitor.check_test_progress()
            monitor.get_summary_stats()
            print("\n" + "=" * 60)
            print("⏱️  30秒後刷新... (Ctrl+C 退出)")
            time.sleep(30)
            os.system('clear' if os.name == 'posix' else 'cls')
            
    except KeyboardInterrupt:
        print("\n🛑 監控停止")

if __name__ == "__main__":
    main()
