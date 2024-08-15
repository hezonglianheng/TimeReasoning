# encoding: utf8
# date: 2024-08-15
# author: Qin Yuhang
# 作为一个示例，这是一个年份问题的自动问题生成器

import timeline

# 创建一个时间线对象
line = timeline.TimeLine("小明", timeline.TimeScale.Year)

# 创建若干事件对象
life = timeline.DurationEvent("活在世上", 1900, 1984) # 人生
# 创建持续事件后，可以设置它的开始和结束事件
life.set_start_event("出生") # 出生
life.set_end_event("去世") # 去世
childhood = timeline.DurationEvent("童年", 1900, 1912) # 童年
middle_school = timeline.DurationEvent("读中学", 1912, 1918) # 中学
middle_school.set_start_event("升入中学") # 升入中学
middle_school.set_end_event("从中学毕业") # 毕业
meet_girl = timeline.PointEvent("遇见未来的妻子", 1921) # 遇见未来的妻子
love = timeline.DurationEvent("恋爱", 1921, 1928) # 恋爱
love.set_end_event("结婚") # 结婚
daughter_life = timeline.DurationEvent("女儿活在世上", 1930, 1972) # 女儿的人生
daughter_life.set_start_event("成为一个女孩的父亲") # 成为一个女孩的父亲
daughter_life.set_end_event("女儿去世") # 女儿去世

# 将事件添加到时间线中
line.add_event(life, childhood, middle_school, meet_girl, love, daughter_life)
print(line.events)

# 运行时间线
result = line.run()
print(result)