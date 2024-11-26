# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

import json
from pathlib import Path
import random
from itertools import combinations
import sys

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import event, scene, constraint, timeknoledge
from timereasoning import timescale as ts

if __name__ == "__main__":
    # 定义事件，注意有控制之后不需要赋时间值
    life = event.DurativeEvent("lived", " his life")
    life.set_start_event("was born", "")
    life.set_end_event("passed away", "")

    primary_school = event.DurativeEvent("studied in", " elementary school")
    primary_school.set_start_event("started", " elementary school")
    primary_school.set_end_event("graduated from", " elementary school")

    middle_school = event.DurativeEvent("studied in", " junior high school")
    middle_school.set_start_event("started", " junior high school")
    middle_school.set_end_event("graduated from", " junior high school")

    high_school = event.DurativeEvent("studied in", " high school")
    high_school.set_start_event("started", " high school")
    high_school.set_end_event("graduated from", " high school")

    university = event.DurativeEvent("studied in", " university")
    university.set_start_event("started", " university")
    university.set_end_event("graduated from", " university")

    meet_wife = event.TemporalEvent("met", " his future wife")

    love = event.DurativeEvent("started", " dating")

    marry = event.TemporalEvent("got married", "")

    be_father = event.TemporalEvent("became", " a father")

    enter = event.TemporalEvent("joined", " a company")
    # be_leader = event.TemporalEvent("became", " a leader")
    retire = event.TemporalEvent("retired", "")

    # 定义约束
    cons = constraint.ConstraintMachine(1900, 2000)
    cons.add_event(life, primary_school, middle_school, high_school, university, meet_wife, love, marry, be_father, enter, retire)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件

    curr_scene = scene.LineScene(ts.TimeScale.Year, "Jack's daughter is telling her friends about the story of his life", lang="en")
    all_combinations = list(combinations((event_list), 6))
    samples = random.sample(all_combinations, 1)
    res = []
    for s in samples:
        # 将事件添加到时间场景中
        curr_scene.add_events(*s)
        # 运行时间场景
        res.extend(curr_scene.run())
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "output.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print("结果成功输出在output.json文件中")