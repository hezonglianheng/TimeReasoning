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
import timereasoning.event as event

relation.DoubleReverseEq.add_props_tuples(
    (timeprop.BeforeP, timeprop.AfterP),
    (timeprop.BeforeTimeP, timeprop.AfterTimeP),
    (timeprop.LongP, timeprop.ShortP),
    (timeprop.LongTimeP, timeprop.ShortTimeP),
    (timeprop.SimultaneousP, timeprop.SimultaneousP),
    (timeprop.GapTimeP, timeprop.GapTimeP),
    (timeprop.SameLenTimeP, timeprop.SameLenTimeP),
)

relation.DoubleEntailment.add_props_tuples(
    (timeprop.BeforeTimeP, timeprop.BeforeP),
    (timeprop.AfterTimeP, timeprop.AfterP),
    (timeprop.LongTimeP, timeprop.LongP),
    (timeprop.ShortTimeP, timeprop.ShortP),
    (timeprop.BeforeTimeP, timeprop.GapTimeP),
    (timeprop.AfterTimeP, timeprop.GapTimeP),
)

class GetSubTimeP(relation.Relation):
    """
    从一个时间命题推断出它的子命题的关系
    """
    @classmethod
    def reason(cls, prop: timeprop.SingleTimeP) -> Optional[List[timeprop.TimeP]]:
        if not isinstance(prop, timeprop.SingleTimeP):
            return None
        return [i for i in prop.get_child_props()]

class GetRelatedTimeP(relation.Relation):
    """
    从一个时间命题推断出它的相关时间命题的关系
    """
    @classmethod
    def reason(cls, prop: timeprop.DurationP) -> Optional[List[timeprop.TimeP]]:
        if isinstance(prop, timeprop.DurationP):
            return [i for i in prop.related_prop]
        else:
            return None

class ReverseDuring(relation.Relation):
    """如果DuringTimeP(A, B)成立，且A, B都是时段，则有DuringTimeP(B, A)成立
    """
    @classmethod
    def reason(cls, prop: timeprop.DuringTimeP) -> Optional[List[timeprop.DuringTimeP]]:
        if not isinstance(prop, timeprop.DuringTimeP):
            return None
        if isinstance(prop.element1, event.DurativeEvent) and isinstance(prop.element2, event.DurativeEvent):
            return [timeprop.DuringTimeP(prop.element2, prop.element1)]
        else:
            return None

class EntailDuring(relation.Relation):
    """如果DuringTimeP(A, B)成立，且A是时点, B是时段，则有After(A, B.element.start_event)和Before(A, B.element.end_event)成立
    """
    @classmethod
    def reason(cls, prop: timeprop.DuringTimeP) -> Optional[List[relation.Relation]]:
        if not isinstance(prop, timeprop.DuringTimeP):
            return None
        if isinstance(prop.element1, event.TemporalEvent) and isinstance(prop.element2, event.DurativeEvent):
            return [timeprop.AfterP(prop.element1, prop.element2.start_event), timeprop.BeforeP(prop.element1, prop.element2.end_event)]
        else:
            return None

# 时间命题的关系列表
RELATIONS: list[type[relation.Relation]] = [
    relation.DoubleReverseEq, 
    relation.DoubleEntailment, 
    GetSubTimeP, 
    GetRelatedTimeP,
    # 增加During相关关系
    ReverseDuring,
    EntailDuring,
]