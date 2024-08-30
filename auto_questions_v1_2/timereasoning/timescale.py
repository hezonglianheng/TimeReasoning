# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
定义时间尺度枚举类，指定命题和问题的翻译方式
"""

import json5
from enum import IntEnum, unique
from pathlib import Path
from typing import Dict, List

@unique
class TimeScale(IntEnum):
    """时间尺度的枚举类
    
    Attributes:
        Order (int): 时间的顺序
        Year (int): 年
        Month (int): 月
        Weekday (int): 星期
        Date (int): 日期
        Hour (int): 小时
        Minute (int): 分钟
    """
    Order = 0
    Year = 1
    Month = 2
    Weekday = 3
    Date = 4
    Hour = 5
    Minute = 6

def choose_templates(scale: TimeScale | int) -> Dict[str, List[str]]:
    """根据时间尺度选择对应的模板
    
    Args:
        scale (TimeScale): 时间尺度
    
    Returns:
        Dict[str, List[str]]: 每种命题对应的模板
    """
    scale = TimeScale(scale) if isinstance(scale, int) else scale
    temp_dir = Path(__file__).resolve().parent / "templates"
    with open(temp_dir / f"{scale.name.lower()}.json5", "r", encoding = "utf-8") as f:
        templates: Dict[str, List[str]] = json5.load(f)
    return templates