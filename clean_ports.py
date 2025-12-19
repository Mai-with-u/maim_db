
import os
import sys
import subprocess
import time

PORTS = [8000, 8081, 18040, 8880, 5173, 8001, 18042, 18045, 8005]

def kill_port(port):
    """尝试清理指定端口的进程"""
    print(f"正在检查端口 {port}...")
    try:
        # 使用 fuser 查找并杀死占用端口的进程
        # -k: kill
        # -9: SIGKILL
        # /tcp: 指定 TCP 端口
        result = subprocess.run(
            ["fuser", "-k", "-9", f"{port}/tcp"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        if result.returncode == 0:
            print(f"✅ 端口 {port} 已被清理")
        else:
            # fuser 返回非0通常意味着没有进程占用该端口
            print(f"⚪ 端口 {port} 未被占用或无需清理")
            
    except Exception as e:
        print(f"❌ 清理端口 {port} 时发生错误: {e}")

def main():
    print("="*30)
    print("开始清理后端服务端口...")
    print(f"目标端口: {PORTS}")
    print("="*30)
    
    for port in PORTS:
        kill_port(port)
        
    print("\n清理完成。")

if __name__ == "__main__":
    main()
