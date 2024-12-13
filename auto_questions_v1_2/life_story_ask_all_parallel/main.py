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
from timereasoning import language as lg

if __name__ == "__main__":
    # 定义事件，注意有控制之后不需要赋时间值
    lang = "zh"
    life = event.DurativeEvent("度过", "一生")
    life.add_name("en", "lived", " his life")
    life.set_start_event("出生", "")
    life.start_event.add_name("en", "was born", "")
    life.set_end_event("去世", "")
    life.end_event.add_name("en", "passed away", "")
    life.duration_event.add_name("en", "lived", " his life")

    primary_school = event.DurativeEvent("上", "小学")
    primary_school.add_name("en", "studied in", " elementary school")
    primary_school.auto_set(lang)
    primary_school.start_event.add_name("en", "started", " elementary school")
    primary_school.set_end_event("小学毕业", "")
    primary_school.end_event.add_name("en", "graduated from", " elementary school")
    primary_school.duration_event.add_name("en", "studied in", " elementary school")

    middle_school = event.DurativeEvent("上", "初中")
    middle_school.add_name("en", "studied in", " junior high school")
    middle_school.auto_set(lang)
    middle_school.start_event.add_name("en", "started", " junior high school")
    middle_school.set_end_event("初中毕业", "")
    middle_school.end_event.add_name("en", "graduated from", " junior high school")
    middle_school.duration_event.add_name("en", "studied in", " junior high school")

    high_school = event.DurativeEvent("上", "高中")
    high_school.add_name("en", "studied in", " high school")
    high_school.auto_set(lang)
    high_school.start_event.add_name("en", "started", " high school")
    high_school.set_end_event("高中毕业", "")
    high_school.end_event.add_name("en", "graduated from", " high school")
    high_school.duration_event.add_name("en", "studied in", " high school")

    university = event.DurativeEvent("上", "大学")
    university.auto_set(lang)
    university.add_name("en", "studied in", " university")
    university.start_event.add_name("en", "started", " university")
    university.set_end_event("大学毕业", "")
    university.end_event.add_name("en", "graduated from", " university")
    university.duration_event.add_name("en", "studied in", " university")

    meet_wife = event.TemporalEvent("遇见", "未来的妻子")
    meet_wife.add_name("en", "met", " his future wife")

    love = event.DurativeEvent("谈", "恋爱")
    love.add_name("en", "started", " dating")
    love.auto_set(lang)
    love.start_event.add_name("en", "started", " dating")
    love.end_event.add_name("en", "ended", " dating")
    love.duration_event.add_name("en", "have", " a romantic relationship")

    marry = event.TemporalEvent("结婚", "")
    marry.add_name("en", "got married", "")

    be_father = event.TemporalEvent("成为", "父亲")
    be_father.add_name("en", "became", " a father")

    enter = event.TemporalEvent("进入", "公司")
    enter.add_name("en", "joined", " a company")
    # be_leader = event.TemporalEvent("成为", "领导")
    retire = event.TemporalEvent("退休", "")
    retire.add_name("en", "retired", "")

    # 定义约束
    cons = constraint.ConstraintMachine(1900, 2000)
    cons.add_event(life, primary_school, middle_school, high_school, university, meet_wife, love, marry, be_father, enter, retire)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
    curr_scene = scene.LineScene(ts.TimeScale.Year, "小明的女儿正在给朋友讲述父亲的一生", ask_mode="deepest")
    lang_scene = lg.TimeParallelScene(curr_scene)
    lang_scene.add_guide("zh", "小明的女儿正在给朋友讲述父亲的一生")
    lang_scene.add_guide("en", "Jack's daughter is telling her friends about the story of his life")
    all_combinations = list(combinations((event_list), 6))
    samples = random.sample(all_combinations, 10)
    res = []
    for s in samples:
        # 将事件添加到时间场景中
        curr_scene.add_events(*s)
        # 添加知识
        curr_scene.add_knowledge()
        # 运行时间场景
        # res.extend(curr_scene.run(1))
        # res.extend(curr_scene.run_ask_all())
        res.extend(lang_scene.run_ask_all())
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "output.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print(f"结果成功输出在{output_file}文件中")