import psutil
import os
import time

# 查找python进程
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if 'python' in proc.info['name'].lower():
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'sanguo-game' in cmdline and 'main.py' in cmdline:
            print(f"找到服务器进程: PID={proc.info['pid']}")
            print(f"命令行: {cmdline}")
            
            # 查找日志文件
            log_files = []
            for root, dirs, files in os.walk('E:\\sanguo-game\\sanguo-game'):
                for file in files:
                    if file.endswith('.log') and 'error' in file.lower() or file.startswith('server'):
                        log_files.append(os.path.join(root, file))
            
            print(f"\n找到的日志文件:")
            for log in log_files:
                print(f"  {log}")
                print(f"  最后修改时间: {time.ctime(os.path.getmtime(log))}")
                print(f"  文件大小: {os.path.getsize(log)} bytes")
                print(f"\n最后10行内容:")
                try:
                    with open(log, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:
                            print(f"  {line.rstrip()}")
                except Exception as e:
                    print(f"  读取失败: {e}")
                print()
