# encoding: utf8
# date: 2024-09-11
# author: Qin Yuhang

import json
from pathlib import Path
import random
from itertools import combinations
import sys

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())
from timereasoning import event, scene
from timereasoning import timescale as ts

if __name__ == "__main__":
    curr_scene = scene.LoopScene(ts.TimeScale.Weekday, "小明是一名大学生，以下是他的每周安排", ask_mode='deepest')
    learn_japanese = event.TemporalEvent("学", "日语", 1)
    date = event.TemporalEvent("约会", "", 5)
    play_badminton = event.TemporalEvent("打", "羽毛球", 3)
    arrange = event.TemporalEvent("整理", "宿舍", 4)
    read_papers = event.TemporalEvent("看", "论文", 6)
    meeting = event.TemporalEvent("开", "组会", 3)
    jogging = event.TemporalEvent("跑步", "", 3)
    movie = event.TemporalEvent("看", "电影", 7)
    enjoy_fiction = event.TemporalEvent("阅读", "科幻小说", 4)
    guitar = event.TemporalEvent("练习", "吉他", 5)
    # 随机抽取事件
    all_combinations = list(combinations((learn_japanese, date, play_badminton, arrange, read_papers, meeting, movie, enjoy_fiction, guitar, jogging), 6))
    samples = random.sample(all_combinations, 10)
    res = []
    for s in samples:
        curr_scene.add_events(*s)
        res.extend(curr_scene.run(1))
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "outputs.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print(f"结果成功输出在{output_file}文件中")