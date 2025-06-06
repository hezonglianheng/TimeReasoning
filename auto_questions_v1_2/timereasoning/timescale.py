# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
定义时间尺度枚举类，指定命题和问题的翻译方式
"""

import json5
from enum import IntEnum, unique
from pathlib import Path
from typing import Dict, List, Optional

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

def choose_templates(scale: TimeScale | int, lang: str = "zh") -> Dict[str, List[str]]:
    """根据时间尺度和语言信息选择对应的模板
    
    Args:
        scale (TimeScale): 时间尺度
        lang (str, optional): 语言. 默认为"zh"(简体中文).
    
    Returns:
        Dict[str, List[str]]: 每种命题对应的模板

    Raises:
        FileNotFoundError: 当指定的语言参数不合法时，未找到对应的模板文件夹抛出
    """
    scale = TimeScale(scale) if isinstance(scale, int) else scale
    temp_dir = Path(__file__).resolve().parent / "templates" / lang
    if not temp_dir.exists():
        raise FileNotFoundError(f"未找到语言{lang}的模板文件夹")
    with open(temp_dir / f"{scale.name.lower()}.json5", "r", encoding = "utf-8") as f:
        templates: Dict[str, List[str]] = json5.load(f)
    return templates

def get_loop_param(scale: TimeScale | int) -> Optional[int]:
    """根据时间尺度获取循环参数

    Args:
        scale (TimeScale | int): 时间尺度

    Returns:
        Optional[int]: 循环参数
    """
    scale = TimeScale(scale) if isinstance(scale, int) else scale
    if scale == TimeScale.Weekday:
        return 7
    elif scale == TimeScale.Month:
        return 12
    elif scale == TimeScale.Date:
        return 30
    elif scale == TimeScale.Hour:
        return 24
    elif scale == TimeScale.Minute:
        return 60
    else:
        return None