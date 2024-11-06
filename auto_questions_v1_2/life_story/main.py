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
    life = event.DurativeEvent("度过", "一生")
    life.set_start_event("出生", "")
    life.set_end_event("去世", "")

    primary_school = event.DurativeEvent("上", "小学")
    primary_school.set_end_event("小学毕业", "")

    middle_school = event.DurativeEvent("上", "初中")
    middle_school.set_end_event("初中毕业", "")

    high_school = event.DurativeEvent("上", "高中")
    high_school.set_end_event("高中毕业", "")

    university = event.DurativeEvent("上", "大学")
    university.set_end_event("大学毕业", "")

    meet_wife = event.TemporalEvent("遇见", "未来的妻子")

    love = event.DurativeEvent("谈", "恋爱")

    marry = event.TemporalEvent("结婚", "")

    be_father = event.TemporalEvent("成为", "父亲")

    enter = event.TemporalEvent("进入", "公司")
    # be_leader = event.TemporalEvent("成为", "领导")
    retire = event.TemporalEvent("退休", "")

    # 定义约束
    cons = constraint.ConstraintMachine(1900, 2000)
    cons.add_event(life, primary_school, middle_school, high_school, university, meet_wife, love, marry, be_father, enter, retire)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
    curr_scene = scene.LineScene(ts.TimeScale.Year, "小明的女儿正在给朋友讲述父亲的一生")
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