# encoding: utf8
# date: 2024-09-11
# author: Qin Yuhang

import json
from pathlib import Path
import random
from itertools import combinations
from timereasoning import event, scene
from timereasoning import timescale as ts

if __name__ == "__main__":
    curr_scene = scene.LoopScene(ts.TimeScale.Weekday, "Jack has a clear weekly plan", lang="en")
    learn_japanese = event.TemporalEvent("learns", " Japanese", 1)
    date = event.TemporalEvent("goes on", " a date", 5)
    play_badminton = event.TemporalEvent("plays", " badminton", 3)
    arrange = event.TemporalEvent("cleans", " his dormitory", 4)
    read_papers = event.TemporalEvent("reads", " essays", 6)
    meeting = event.TemporalEvent("has", " a meeting", 3)
    jogging = event.TemporalEvent("does", " some exercises", 3)
    movie = event.TemporalEvent("watches", " movies", 7)
    enjoy_fiction = event.TemporalEvent("reads", " sci-fi novels", 4)
    guitar = event.TemporalEvent("practices", " the guitar", 5)
    # 随机抽取事件
    all_combinations = list(combinations((learn_japanese, date, play_badminton, arrange, read_papers, meeting, movie, enjoy_fiction, guitar, jogging), 6))
    samples = random.sample(all_combinations, 10)
    res = []
    for s in samples:
        curr_scene.add_events(*s)
        res.extend(curr_scene.run())
        curr_scene.reset()
    output_file = Path(__file__).resolve().parents[0] / "outputs" /"loopoutput.json"
    with output_file.open('w', encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    print("结果成功输出在outputs/loopoutput.json文件中")