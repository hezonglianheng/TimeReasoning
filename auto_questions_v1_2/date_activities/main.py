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
    start = event.TemporalEvent("开始记录", "7月日记", 1)
    end = event.TemporalEvent("结束记录", "7月日记", 31)

    paper_outline = event.DurativeEvent("撰写", "课程论文大纲")
    paper_outline.set_end_event("完成", "课程论文大纲")

    paper_writing = event.DurativeEvent("撰写", "课程论文")
    paper_writing.set_end_event("写完并提交", "课程论文")

    meeting = event.DurativeEvent("准备", "组会报告")
    meeting.set_end_event("做", "组会报告")

    meet_friends = event.DurativeEvent("和朋友去外地旅行", "")
    meet_friends.set_end_event("结束", "和朋友的旅行")

    watch_movie = event.TemporalEvent("观看", "最新上映的电影")

    basketball_game = event.TemporalEvent("参加", "篮球比赛")

    video_game = event.TemporalEvent("打了", "几乎一整天电脑游戏")

    # 定义约束
    cons = constraint.ConstraintMachine(1, 31)
    cons.add_event(start, end, paper_outline, paper_writing, meeting, meet_friends, watch_movie, basketball_game, video_game)
    cons.read_constraints(Path(__file__).resolve().parents[0] / "constraint_date.json5")
    event_list = cons.run()

    # 定义场景
    # 随机抽取事件
    curr_scene = scene.LineScene(ts.TimeScale.Date, "小明度过了繁忙的7月，他在每一天都用日记本记录下自己完成的事情")
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