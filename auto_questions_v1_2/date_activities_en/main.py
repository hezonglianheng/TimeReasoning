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
    start = event.TemporalEvent("started recording", " the journal of May", 1)
    end = event.TemporalEvent("finished recording", " the journal of May", 31)

    paper_outline = event.DurativeEvent("wrote", " the outline of a course paper")
    paper_outline.set_start_event("started writing", " an outline of a course paper")
    paper_outline.set_end_event("finished writing", " the outline of the course paper")

    paper_writing = event.DurativeEvent("wrote", " the course paper")
    paper_writing.set_start_event("started writing", " the course paper")
    paper_writing.set_end_event("finished writing and submitted", " the course paper")

    meeting = event.DurativeEvent("prepared for", " the group meeting report")
    meeting.set_start_event("started preparing for", " the report of the group meeting")
    meeting.set_end_event("delivered", " the group meeting report")

    meet_friends = event.DurativeEvent("went on", " a trip with his friends")
    meet_friends.set_start_event("started", " a trip with friends")
    meet_friends.set_end_event("finished", " the trip with his friends")

    watch_movie = event.TemporalEvent("watched", " the latest released movie")

    basketball_game = event.TemporalEvent("participated in", " a basketball game")

    video_game = event.TemporalEvent("played", " computer games for almost an entire day")

    # 定义约束
    cons = constraint.ConstraintMachine(1, 31)
    cons.add_event(start, end, paper_outline, paper_writing, meeting, meet_friends, watch_movie, basketball_game, video_game)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
    curr_scene = scene.LineScene(ts.TimeScale.Date, "Jack had a busy May, and he has recorded everything he did in a journal", lang="en")
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