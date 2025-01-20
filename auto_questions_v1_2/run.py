# encoding: utf8
# date: 2024-11-30
# 多进程运行脚本的脚本

import subprocess
from pathlib import Path

script_paths = [
    "life_story_parallel/main.py",
    "life_story_ask_all_parallel/main.py",
    "life_story_ask_all_parallel_neg/main.py",
    "week_schedule_parallel/main.py",
    "week_schedule_askall_parallel/main.py",
    "week_schedule_askall_neg_parallel/main.py",
]

if __name__ == "__main__":
    for script_path in script_paths:
        script_path = Path(__file__).resolve().parent / script_path
        command = f"nohup python {script_path.as_posix()} &"
        subprocess.Popen(command, shell=True)
        print(f"启动 {script_path} 成功")