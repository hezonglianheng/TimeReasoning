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
<<<<<<< HEAD
    start = event.TemporalEvent("开始记录", "新一年的日记")
    end = event.TemporalEvent("结束记录", "本年的日记")

    thesis_defense = event.DurativeEvent("准备", "答辩")
    # thesis_defense.set_start_event("开始", "准备答辩")
    thesis_defense.set_end_event("通过", "答辩")

    internship = event.DurativeEvent("线上实习", "")
    # internship.set_start_event("开始", "线上实习")
    internship.set_end_event("顺利离职", "")

    traveling = event.DurativeEvent("出国旅行", "")
    # traveling.set_start_event("开始", "出国旅行")
    traveling.set_end_event("旅行结束", "")

    novel_writing = event.DurativeEvent("创作", "小说")
    # novel_writing.set_start_event("开始", "创作小说")
    novel_writing.set_end_event("小说发表", "")

    win_lottery = event.TemporalEvent("抽中", "彩票")

    class_reunion = event.TemporalEvent("参加", "同学聚会")

    concert = event.TemporalEvent("听", "音乐会")
=======
    start = event.TemporalEvent("started", " the journal of this year")
    end = event.TemporalEvent("ended", " the journal of this year")

    thesis_defense = event.DurativeEvent("prepared for", " the thesis defense")
    thesis_defense.set_start_event("started preparing for", " the thesis defense")
    thesis_defense.set_end_event("passed", " the thesis defense")

    internship = event.DurativeEvent("had", " an online internship")
    internship.set_start_event("started", " an online internship")
    internship.set_end_event("successfully ended", " the internship")

    traveling = event.DurativeEvent("had", " an overseas trip")
    traveling.set_start_event("started", " an overseas trip")
    traveling.set_end_event("ended", " the overseas trip")

    novel_writing = event.DurativeEvent("wrote", " a novel")
    novel_writing.set_start_event("started writing", " a novel")
    novel_writing.set_end_event("published", " his own novel")

    win_lottery = event.TemporalEvent("won", " the lottery")

    class_reunion = event.TemporalEvent("attended", " a class reunion")

    concert = event.TemporalEvent("attended", " a concert")
>>>>>>> b5f9fe3 (中英转换及llm测试)

    # 定义约束
    cons = constraint.ConstraintMachine(1, 12)
    cons.add_event(start, end, thesis_defense, internship, traveling, novel_writing, win_lottery, class_reunion, concert)
<<<<<<< HEAD
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint_month.json5")
=======
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
>>>>>>> b5f9fe3 (中英转换及llm测试)
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
<<<<<<< HEAD
    curr_scene = scene.LineScene(ts.TimeScale.Month, "小明今年坚持每天写日记。在辞旧迎新之际，他翻开日记本，回忆自己充实的一年")
=======
    curr_scene = scene.LineScene(ts.TimeScale.Month, "Jack has kept writing journal during this year. As the year comes to a close, he opens his journal and reflects on his fulfilling year", lang="en")
>>>>>>> b5f9fe3 (中英转换及llm测试)
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