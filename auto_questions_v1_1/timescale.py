# encoding: utf8
# date: 2024-08-22
# author: Qin Yuhang
# 定义了时间尺度

from enum import Enum, unique

@unique
class TimeScale(Enum):
    """时间尺度枚举类
    
    Attributes:
        Order (int): 事件的顺序
        Year (int): 年份
    """
    Order = 0 # 事件的顺序
    Year = 1 # 年份