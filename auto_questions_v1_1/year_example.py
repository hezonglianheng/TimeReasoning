# encoding: utf8
# date: 2024-08-18
# 年份问题示例

import timescale as scale
import timeline
import statements as stmt
from pathlib import Path
import json

# 创建一个时间线对象
line = timeline.TimeLine(scale.TimeScale.Year)
# 设置引导语。引导语也可以在创建时间线对象时设置
line.add_guide("你来到一座坟墓面前。这座坟墓的主人的生活经历如下：")
# 设置事件
life = stmt.LastingEvent("度过", "他的一生", 1900, 1984)
life.set_start_event("出生", "") # 可以为持续事件设置特殊的起始事件
life.set_end_event("去世", "") # 可以为持续事件设置特殊的结束事件
childhood = stmt.LastingEvent("度过", "童年", 1900, 1912)
middle_school = stmt.LastingEvent("读", "中学", 1912, 1918)
middle_school.set_start_event("升入", "中学")
middle_school.set_end_event("从中学毕业", "")
meet_wife = stmt.TemporalEvent("遇见", "未来的妻子", 1921)
love = stmt.LastingEvent("和未来的妻子恋爱", "", 1921, 1928)
love.set_end_event("结婚", "")
daughter_life = stmt.LastingEvent("女儿度过", "一生", 1930, 1972)
daughter_life.set_start_event("成为", "女孩的父亲")
daughter_life.set_end_event("女儿去世", "")

# 将事件添加到时间线中
line.add_events(life, childhood, middle_school, meet_wife, love, daughter_life)

# 运行时间线并存入output文件中
if __name__ == "__main__":
    path = Path(__file__).parent / "outputs" / "year.json"
    result_list: list[dict] = []
    for i in range(10):
        result_list.append(line.run(verbose=2))
    with path.open("w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)