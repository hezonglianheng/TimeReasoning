# encoding: utf8
# date: 2024-08-26
# author: Qin Yuhang

import sys
from pathlib import Path
from typing import Optional, List

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.relation as relation
import timereasoning.timeprop as timeprop

class TimeEquivalence(relation.Equivalence):
    """
    时间命题的等价关系\n
    类型元组代表的关系为: prop1 <-> prop2
    """
    tp_tuples: list[tuple[type[timeprop.DoubleTimeP], type[timeprop.DoubleTimeP]]] = [
        (timeprop.BeforeP, timeprop.AfterP),
        (timeprop.BeforeTimeP, timeprop.AfterTimeP),
        (timeprop.LongP, timeprop.ShortP),
        (timeprop.LongTimeP, timeprop.ShortTimeP),
    ]

    @classmethod
    def reason(cls, prop: timeprop.TimeP) -> Optional[List[timeprop.TimeP]]:
        if isinstance(prop, timeprop.DoubleTimeP):
            if prop.symmetrical: # 如果是对称的，交换两个时间命题的位置
                return [prop.swap()]
            else:
                res: List[timeprop.TimeP] = []
                for tp1, tp2 in cls.tp_tuples: # 遍历所有的类型元组
                    if isinstance(prop, tp1): # 如果输入的时间命题是第一个类型元组的子类，则返回第二个类型元组的实例
                        res.append(tp2(prop.prev_element, prop.new_element))
                    if isinstance(prop, tp2): # 如果输入的时间命题是第二个类型元组的子类，则返回第一个类型元组的实例
                        res.append(tp1(prop.prev_element, prop.new_element))
                return res # 返回推理出的时间命题
        else:
            return None

class TimeEntailment(relation.Entailment):
    """
    时间命题的蕴含关系\n
    类型元组代表的关系为: prop1 -> prop2
    """
    tp_tuples: list[tuple[type[timeprop.DoubleTimeP], type[timeprop.DoubleTimeP]]] = [
        (timeprop.BeforeTimeP, timeprop.BeforeP),
        (timeprop.AfterTimeP, timeprop.AfterP),
        (timeprop.LongTimeP, timeprop.LongP),
        (timeprop.ShortTimeP, timeprop.ShortP),
        (timeprop.BeforeTimeP, timeprop.GapTimeP),
        (timeprop.AfterTimeP, timeprop.GapTimeP),
    ]

    @classmethod
    def reason(cls, prop: timeprop.TimeP) -> List[timeprop.TimeP] | None:
        if isinstance(prop, timeprop.DoubleTimeP):
            res: List[timeprop.TimeP] = []
            for tp1, tp2 in cls.tp_tuples:
                if isinstance(prop, tp1):
                    res.append(tp2(prop.new_element, prop.prev_element))
            return res
        elif isinstance(prop, (timeprop.DurativeP, timeprop.FreqP)): # 如果是持续时间命题或频率命题
            return [i for i in prop.get_child_props()]
        else:
            return None

    @classmethod
    def judge(cls, prop1: timeprop.TimeP, prop2: timeprop.TimeP) -> bool:
        # 如果prop2和prop1的子命题相等，则返回True
        if isinstance(prop2, (timeprop.SubTemporalP, timeprop.DurationP)):
            if isinstance(prop1, (timeprop.DurativeP, timeprop.FreqP)):
                if prop2.parent_event == prop1.element:
                    return True
        return super().judge(prop1, prop2)

# 时间命题的关系列表
RELATIONS: list[type[relation.Relation]] = [TimeEquivalence, TimeEntailment]