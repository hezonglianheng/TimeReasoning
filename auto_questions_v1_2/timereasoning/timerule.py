# encoding: utf8
# date: 2024-08-25
# author: Qin Yuhang

"""
关于时间命题推理规则的基本定义和基本操作
"""

import sys
from pathlib import Path
import abc
from typing import Optional

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.rule as rule
import timereasoning.timeprop as timeprop

class TimeRule(rule.Rule):
    @classmethod
    @abc.abstractmethod
    def reason(cls, prop1: timeprop.TimeP, prop2: timeprop.TimeP) -> Optional[timeprop.TimeP]:
        """根据时间命题推理生成新的时间命题

        Args:
            prop1 (TimeP): 时间命题1
            prop2 (TimeP): 时间命题2

        Returns:
            TimeP: 新的时间命题
        """
        pass

class Single2DoubleR(TimeRule):
    """
    从两个单元素命题推出一个双元素命题的规则\n
    推导方式: F(x) && F(y) -> G(x, y)
    """
    @classmethod
    def reason(cls, prop1: timeprop.SingleTimeP, prop2: timeprop.SingleTimeP) -> timeprop.TimeP | None:
        if not all([isinstance(i, timeprop.SingleTimeP) for i in [prop1, prop2]]):
            return None
        if prop1 == prop2:
            return None
        return timeprop.DoubleTimeP.build(prop1.element, prop2.element)

class TransitivityR(TimeRule):
    """
    传递性推理规则\n
    推导方式: F(x, y) && F(y, z) -> F(x, z)
    """
    tps: type[timeprop.DoubleTimeP] = [
        timeprop.BeforeP,
        timeprop.BeforeTimeP,
        timeprop.AfterP,
        timeprop.AfterTimeP,
        timeprop.SimultaneousP,
        timeprop.LongP,
        timeprop.LongTimeP,
        timeprop.ShortP,
        timeprop.ShortTimeP,
        timeprop.SameLenTimeP,
    ]

    @classmethod
    def add_tps(cls, *tps: type[timeprop.DoubleTimeP]):
        """添加新的有传递性的时间命题类型"""
        cls.tps += tps
    
    @classmethod
    def reason(cls, prop1: timeprop.TimeP, prop2: timeprop.TimeP) -> timeprop.TimeP | None:
        if type(prop1) != type(prop2):
            return None
        for tp in cls.tps:
            if isinstance(prop1, tp) and prop1.prev_element == prop2.new_element and prop1.new_element != prop2.prev_element:
                return tp(prop1.new_element, prop2.prev_element)
        return None

class SingleDouble2SingleR(TimeRule):
    """
    一单元素命题和一双元素命题推一单元素命题\n
    推导方式: \n
    F(x) && G(x, y) -> F(y)\n
    F(y) && G(x, y) -> F(x)
    """
    @classmethod
    def reason(cls, prop1: timeprop.SingleTimeP, prop2: timeprop.DoubleTimeP) -> timeprop.TimeP | None:
        if not (isinstance(prop1, timeprop.TemporalP) and isinstance(prop2, timeprop.DoubleTimeP)):
            return None # 如果prop1不是单元素时间命题或者prop2不是双元素时间命题，则返回None
        if not prop2.precise:
            return None # 如果prop2非精确，则无法进行推导
        else:
            if prop1.element == prop2.prev_element:
                return timeprop.SingleTimeP.build(prop2.new_element)
            elif prop1.element == prop2.new_element:
                return timeprop.SingleTimeP.build(prop2.prev_element)
            else:
                return None

# 时间推理规则列表
RULES: list[type[TimeRule]] = [Single2DoubleR, TransitivityR, SingleDouble2SingleR]