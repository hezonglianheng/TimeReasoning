# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

import json
from pathlib import Path
import random
from itertools import combinations
from timereasoning import event, scene
from timereasoning import timescale as ts

if __name__ == "__main__": # 程序入口，必须使用这个结构
    # 创建一个时间场景
    curr_scene = scene.LineScene(ts.TimeScale.Year, "时间推理")
    # 添加事件
    life = event.DurativeEvent("度过", "一生", 1900, 1984)
    life.set_start_event("出生", "")
    life.set_end_event("去世", "")

    meet_wife = event.TemporalEvent("遇见", "未来的妻子", 1921)

    university = event.DurativeEvent("读", "大学", 1920, 1924)
    university.set_start_event("入学", "")
    university.set_end_event("毕业", "")

    be_a_teacher = event.TemporalEvent("成为", "教师", 1924)

    fall_in_love = event.DurativeEvent("谈", "恋爱", 1924, 1932)
    fall_in_love.set_end_event("结婚", "")

    be_father = event.TemporalEvent("成为", "父亲", 1933)
    be_president = event.TemporalEvent("当上", "校长", 1953)
    retired = event.TemporalEvent("退休", "", 1964)
    be_grandfather = event.TemporalEvent("成为", "爷爷", 1971)
    # 随机抽取事件
    all_combinations = list(combinations((life, meet_wife, university, be_a_teacher, fall_in_love, be_father, be_president, be_grandfather, retired), 6))
    samples = random.sample(all_combinations, 1)
    res = []
    for s in samples:
        # 将事件添加到时间场景中
        curr_scene.add_events(*s)
        # 运行时间场景
        res.extend(curr_scene.run())
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "outputs" / "output.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print("结果成功输出在outputs/output.json文件中")