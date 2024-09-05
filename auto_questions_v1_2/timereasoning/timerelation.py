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

# 时间命题的关系列表
RELATIONS: list[type[relation.Relation]] = [
    relation.DoubleReverseEq, 
    relation.DoubleEntailment, 
    GetSubTimeP, 
    GetRelatedTimeP,
]