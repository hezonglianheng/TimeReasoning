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
    # 1-20新增：增加对随机seed的控制
    random.seed(0)
    # 定义事件，注意有控制之后不需要赋时间值
    lang = "zh"
    life = event.DurativeEvent("他度过", "一生")
    life.add_name("en", "Jack lived", " his life")
    life.set_start_event("他出生", "")
    life.start_event.add_name("en", "Jack was born", "")
    life.set_end_event("他去世", "")
    life.end_event.add_name("en", "Jack passed away", "")
    life.duration_event.add_name("en", "Jack lived", " his life")

    primary_school = event.DurativeEvent("他上", "小学")
    primary_school.add_name("en", "Jack studied in", " elementary school")
    primary_school.auto_set(lang)
    primary_school.set_start_event("他开始上小学", "")
    primary_school.start_event.add_name("en", "Jack started", " elementary school")
    primary_school.set_end_event("他小学毕业", "")
    primary_school.end_event.add_name("en", "Jack graduated from", " elementary school")
    primary_school.duration_event.add_name("en", "Jack studied in", " elementary school")

    middle_school = event.DurativeEvent("他上", "初中")
    middle_school.add_name("en", "Jack studied in", " junior high school")
    middle_school.auto_set(lang)
    middle_school.set_start_event("他开始上初中", "")
    middle_school.start_event.add_name("en", "Jack started", " junior high school")
    middle_school.set_end_event("他初中毕业", "")
    middle_school.end_event.add_name("en", "Jack graduated from", " junior high school")
    middle_school.duration_event.add_name("en", "Jack studied in", " junior high school")

    high_school = event.DurativeEvent("他上", "高中")
    high_school.add_name("en", "Jack studied in", " high school")
    high_school.auto_set(lang)
    high_school.set_start_event("他开始上高中", "")
    high_school.start_event.add_name("en", "Jack started", " high school")
    high_school.set_end_event("他高中毕业", "")
    high_school.end_event.add_name("en", "Jack graduated from", " high school")
    high_school.duration_event.add_name("en", "Jack studied in", " high school")

    university = event.DurativeEvent("他上", "大学")
    university.auto_set(lang)
    university.add_name("en", "Jack studied in", " university")
    university.set_start_event("他开始上大学", "")
    university.start_event.add_name("en", "Jack started", " university")
    university.set_end_event("他大学毕业", "")
    university.end_event.add_name("en", "Jack graduated from", " university")
    university.duration_event.add_name("en", "Jack studied in", " university")

    meet_wife = event.TemporalEvent("他遇见", "未来的妻子")
    meet_wife.add_name("en", "Jack met", " his future wife")

    love = event.DurativeEvent("他谈", "恋爱")
    love.add_name("en", "Jack was in", " a romantic relationship")
    love.auto_set(lang)
    love.set_start_event("他开始谈恋爱", "")
    love.start_event.add_name("en", "Jack started", " dating")
    love.set_end_event("他结束谈恋爱", "")
    love.end_event.add_name("en", "Jack ended", " his romantic relationship")
    love.duration_event.add_name("en", "Jack was in", " a romantic relationship")

    marry = event.TemporalEvent("他结婚", "")
    marry.add_name("en", "Jack got married", "")

    be_father = event.TemporalEvent("他成为", "父亲")
    be_father.add_name("en", "Jack became", " a father")

    enter = event.TemporalEvent("他进入", "公司")
    enter.add_name("en", "Jack started working at", " a company")
    # be_leader = event.TemporalEvent("他成为", "领导")
    retire = event.TemporalEvent("他退休", "")
    retire.add_name("en", "Jack retired", "")

    # 定义约束
    cons = constraint.ConstraintMachine(1900, 2000)
    cons.add_event(life, primary_school, middle_school, high_school, university, meet_wife, love, marry, be_father, enter, retire)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
    curr_scene = scene.LineScene(ts.TimeScale.Year, "小明的女儿正在给朋友讲述父亲的一生", ask_mode="random")
    lang_scene = lg.TimeParallelScene(curr_scene)
    lang_scene.add_guide("zh", "小明的女儿正在给朋友讲述父亲的一生")
    lang_scene.add_guide("en", "Jack's daughter is telling her friends about the story of her father's life")
    all_combinations = list(combinations((event_list), 6))
    samples = random.sample(all_combinations, 40)
    res = []
    for i, s in enumerate(samples):
        # 将事件添加到时间场景中
        curr_scene.add_events(*s)
        # 添加知识
        curr_scene.add_knowledge()
        # 运行时间场景
        # res.extend(curr_scene.run(1))
        # res.extend(curr_scene.run_ask_all())
        curr_res = lang_scene.run()
        curr_res = [r | {"group": f"life-story-{i}"} for r in curr_res]
        res.extend(curr_res)
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "output.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print(f"结果成功输出在{output_file}文件中")