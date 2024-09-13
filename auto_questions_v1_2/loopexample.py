# encoding: utf8
# date: 2024-09-11
# author: Qin Yuhang

import json
from pathlib import Path
from timereasoning import event, scene
from timereasoning import timescale as ts

if __name__ == "__main__":
    curr_scene = scene.LoopScene(ts.TimeScale.Weekday, "时间推理")
    learn_japanese = event.TemporalEvent("学", "日语", 1)
    date = event.TemporalEvent("约会", "", 5)
    play_badminton = event.TemporalEvent("打", "羽毛球", 3)
    arrange = event.TemporalEvent("整理", "宿舍", 4)
    curr_scene.add_events(learn_japanese, date, play_badminton, arrange)
    res = curr_scene.run()
    output_file = Path(__file__).resolve().parents[0] / "loopoutput.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print("结果成功输出在loopoutput.json文件中")