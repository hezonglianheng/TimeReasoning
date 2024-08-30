# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

import json
from pathlib import Path
from timereasoning import event, scene
from timereasoning import timescale as ts

if __name__ == "__main__": # 程序入口，必须使用这个结构
    # 创建一个时间场景
    curr_scene = scene.TimeScene(ts.TimeScale.Year, "时间推理")
    # 添加事件
    life = event.DurativeEvent("度过", "一生", 1900, 1984)
    life.set_start_event("出生", "")
    life.set_end_event("去世", "")
    meet_wife = event.TemporalEvent("遇见", "未来的妻子", 1921)
    # 将事件添加到时间场景中
    curr_scene.add_events(life, meet_wife)
    # 运行时间场景
    res = curr_scene.run()
    output_file = Path(__file__).resolve().parents[0] / "output.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print("结果成功输出在output.json文件中")