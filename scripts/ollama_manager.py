import subprocess
import sys

def start_ollama():
    """啟動 Ollama 服務"""
    try:
        subprocess.Popen(["ollama", "serve"])
        print("Ollama 服務已啟動。")
    except Exception as e:
        print(f"啟動 Ollama 失敗: {e}", file=sys.stderr)

def stop_ollama():
    """關閉 Ollama 服務"""
    try:
        subprocess.run(["pkill", "-f", "ollama"], check=True)
        print("Ollama 服務已關閉。")
    except Exception as e:
        print(f"關閉 Ollama 失敗: {e}", file=sys.stderr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ollama 服務管理工具")
    parser.add_argument("action", choices=["start", "stop"], help="啟動或關閉 Ollama")
    args = parser.parse_args()

    if args.action == "start":
        start_ollama()
    elif args.action == "stop":
        stop_ollama()