import subprocess
import time
import signal
import os
import logging
import requests
from pathlib import Path
from typing import List

class OllamaManager:
    def __init__(self, startup_timeout=30, health_check_interval=5):
        self.service_pid = None
        self.is_running = False
        self.startup_timeout = startup_timeout
        self.health_check_interval = health_check_interval
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌系統"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger("ollama_manager")
        handler = logging.FileHandler(log_dir / "ollama.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
        
    def start_service(self) -> bool:
        """啟動 Ollama 服務"""
        if self.is_running:
            self.logger.info("Ollama 服務已在運行中")
            return True
            
        self.logger.info("正在啟動 Ollama 服務...")
        try:
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.service_pid = process.pid
            
            # 等待服務啟動
            start_time = time.time()
            while time.time() - start_time < self.startup_timeout:
                if self.check_health():
                    self.is_running = True
                    self.logger.info("Ollama 服務啟動成功")
                    return True
                time.sleep(1)
                
            self.logger.error("Ollama 服務啟動超時")
            return False
        except Exception as e:
            self.logger.error(f"啟動 Ollama 服務失敗: {e}")
            return False
            
    def stop_service(self) -> bool:
        """停止 Ollama 服務"""
        if not self.is_running:
            self.logger.info("Ollama 服務未運行")
            return True
            
        try:
            if self.service_pid:
                os.kill(self.service_pid, signal.SIGTERM)
            else:
                subprocess.run(["pkill", "-f", "ollama"])
            
            self.is_running = False
            self.service_pid = None
            self.logger.info("Ollama 服務已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止 Ollama 服務失敗: {e}")
            return False
            
    def check_health(self) -> bool:
        """檢查 Ollama 服務健康狀態"""
        try:
            response = requests.get("http://localhost:11434/api/health")
            return response.status_code == 200
        except:
            return False
            
    def list_models(self) -> List[str]:
        """列出已安裝的模型"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            return [line.split()[0] for line in result.stdout.splitlines()[1:]]
        except Exception as e:
            self.logger.error(f"列出模型失敗: {e}")
            return []
            
    def pull_model(self, model_name: str) -> bool:
        """下載指定模型"""
        try:
            self.logger.info(f"正在下載模型: {model_name}")
            subprocess.run(["ollama", "pull", model_name], check=True)
            self.logger.info(f"模型 {model_name} 下載完成")
            return True
        except Exception as e:
            self.logger.error(f"下載模型 {model_name} 失敗: {e}")
            return False
            
    def ensure_model_available(self, model_name: str) -> bool:
        """確保指定模型可用"""
        if model_name in self.list_models():
            return True
        return self.pull_model(model_name)

    def __enter__(self):
        self.start_service()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_service()
        
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ollama 服務管理工具")
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "list", "pull"],
        help="要執行的操作"
    )
    parser.add_argument("--model", help="模型名稱（用於 pull 操作）")
    args = parser.parse_args()
    
    manager = OllamaManager()
    
    if args.action == "start":
        manager.start_service()
    elif args.action == "stop":
        manager.stop_service()
    elif args.action == "status":
        status = "運行中" if manager.check_health() else "已停止"
        print(f"Ollama 服務狀態: {status}")
    elif args.action == "list":
        models = manager.list_models()
        print("已安裝的模型:")
        for model in models:
            print(f"- {model}")
    elif args.action == "pull" and args.model:
        manager.pull_model(args.model)

if __name__ == "__main__":
    main()