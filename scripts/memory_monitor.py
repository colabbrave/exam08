import psutil
import time
import sys
import logging
from pathlib import Path
from datetime import datetime

class MemoryMonitor:
    def __init__(self, warning_threshold=80, critical_threshold=90, interval=10):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.interval = interval
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger("memory_monitor")
        handler = logging.FileHandler(log_dir / "memory.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [記憶體使用率: %(memory_usage).1f%%] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
        
    def get_memory_usage(self):
        """獲取當前記憶體使用百分比"""
        return psutil.virtual_memory().percent
        
    def log_memory_status(self, memory_usage):
        """記錄記憶體狀態"""
        extra = {"memory_usage": memory_usage}
        if memory_usage >= self.critical_threshold:
            self.logger.critical("記憶體使用超過臨界值！", extra=extra)
        elif memory_usage >= self.warning_threshold:
            self.logger.warning("記憶體使用超過警告值", extra=extra)
        else:
            self.logger.info("記憶體使用正常", extra=extra)
            
    def start_monitoring(self):
        """開始監控記憶體使用"""
        print(f"開始監控記憶體使用情況 (警告：{self.warning_threshold}%, 臨界：{self.critical_threshold}%)")
        try:
            while True:
                memory_usage = self.get_memory_usage()
                self.log_memory_status(memory_usage)
                
                # 在控制台顯示
                status = (
                    "🔴 危險"
                    if memory_usage >= self.critical_threshold
                    else "⚠️ 警告"
                    if memory_usage >= self.warning_threshold
                    else "✅ 正常"
                )
                print(f"\r記憶體使用: {memory_usage:.1f}% [{status}]", end="")
                
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n記憶體監控已停止")
            
def main():
    import argparse
    parser = argparse.ArgumentParser(description="記憶體監控工具")
    parser.add_argument("--warning", type=float, default=80, help="警告門檻（%）")
    parser.add_argument("--critical", type=float, default=90, help="臨界門檻（%）")
    parser.add_argument("--interval", type=int, default=10, help="檢查間隔（秒）")
    args = parser.parse_args()
    
    monitor = MemoryMonitor(
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        interval=args.interval
    )
    monitor.start_monitoring()

if __name__ == "__main__":
    main()