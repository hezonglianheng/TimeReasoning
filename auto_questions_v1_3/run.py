# encoding: utf8
# date: 2025-05-03
# 在Linux上多进程运行脚本的脚本

import subprocess
from pathlib import Path

setting_dirs = [
    r"setting_dirs/life_story", 
    r"setting_dirs/week_schedule", 
]
question_type = [
    "precise", 
    "correct",
    "incorrect",
]

if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.resolve()
    # 主脚本路径
    main_script_path = current_dir / "main.py"
    # 检查主脚本是否存在
    if not main_script_path.exists():
        raise FileNotFoundError(f"主脚本 {main_script_path} 不存在。请检查路径。")
    
    # 遍历每个设置目录
    for setting_dir in setting_dirs:
        # 构建完整的路径
        full_path = current_dir / setting_dir
        
        # 使用subprocess.run()执行命令
        for typ in question_type:
            # 05-04新增：检查旧的log文件，若存在，则删除
            log_file = full_path / f"{typ}.log"
            if log_file.exists():
                print(f"Deleting old log file: {log_file}")
                log_file.unlink()
            # 构建命令
            command = f"nohup python3 {main_script_path} {full_path} -q {typ} > /dev/null 2>&1 &"
            print(f"Executing command: {command}")
            subprocess.run(command, shell=True, check=True)
