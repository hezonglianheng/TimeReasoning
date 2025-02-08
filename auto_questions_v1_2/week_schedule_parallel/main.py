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
from timereasoning import language as lg

if __name__ == "__main__":
    # 1-20新增：增加对随机seed的控制
    random.seed(0)
    lang = "zh"
    learn_japanese = event.TemporalEvent("他学", "日语", 1)
    learn_japanese.add_name("en", "Jack learns", " Japanese")
    date = event.TemporalEvent("他约会", "", 5)
    date.add_name("en", "Jack goes on", " a date")
    play_badminton = event.TemporalEvent("他打", "羽毛球", 3)
    play_badminton.add_name("en", "Jack plays", " badminton")
    arrange = event.TemporalEvent("他整理", "宿舍", 4)
    arrange.add_name("en", "Jack cleans", " his dormitory room")
    read_papers = event.TemporalEvent("他看", "论文", 6)
    read_papers.add_name("en", "Jack reads", " research papers")
    meeting = event.TemporalEvent("他开", "组会", 3)
    meeting.add_name("en", "Jack has", " a group meeting")
    jogging = event.TemporalEvent("他跑步", "", 3)
    jogging.add_name("en", "Jack goes", " jogging")
    movie = event.TemporalEvent("他看", "电影", 7)
    movie.add_name("en", "Jack watches", " a movie")
    enjoy_fiction = event.TemporalEvent("他阅读", "科幻小说", 4)
    enjoy_fiction.add_name("en", "Jack reads", " sci-fi novels")
    guitar = event.TemporalEvent("他练习", "吉他", 5)
    guitar.add_name("en", "Jack practices", " the guitar")
    # 随机抽取事件
    curr_scene = scene.LoopScene(ts.TimeScale.Weekday, "小明是一名大学生，以下是他的每周安排")
    lang_scene = lg.TimeParallelScene(curr_scene)
    lang_scene.add_guide("zh", "小明是一名大学生，以下是他的每周安排")
    lang_scene.add_guide("en", "Jack is a college student, and here are his weekly plans")
    all_combinations = list(combinations((learn_japanese, date, play_badminton, arrange, read_papers, meeting, movie, enjoy_fiction, guitar, jogging), 6))
    samples = random.sample(all_combinations, 40)
    res = []
    for i, s in enumerate(samples):
        curr_scene.add_events(*s)
        curr_res = lang_scene.run()
        curr_res = [r | {"group": f"week-schedule-{i}"} for r in curr_res]
        res.extend(curr_res)
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "outputs.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print(f"结果成功输出在{output_file}文件中")