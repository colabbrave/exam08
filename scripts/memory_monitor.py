import psutil
import time
import sys

def monitor_memory(threshold_gb=6.0, interval_sec=5):
    """
    持續監控系統記憶體使用狀況，若超過指定門檻則顯示警告。
    :param threshold_gb: 記憶體使用警告門檻（GB）
    :param interval_sec: 檢查間隔秒數
    """
    threshold_bytes = threshold_gb * 1024 * 1024 * 1024
    try:
        while True:
            mem = psutil.virtual_memory()
            used = mem.total - mem.available
            print(f"已用記憶體：{used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB")
            if used > threshold_bytes:
                print(f"警告：記憶體使用超過 {threshold_gb} GB！", file=sys.stderr)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("記憶體監控已停止。")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="記憶體監控工具")
    parser.add_argument("--threshold", type=float, default=6.0, help="警告門檻（GB）")
    parser.add_argument("--interval", type=int, default=5, help="檢查間隔（秒）")
    args = parser.parse_args()
    monitor_memory(args.threshold, args.interval)