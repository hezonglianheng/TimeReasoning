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

from proposition.prop import DoubleProp, SingleProp
import proposition.rule as rule
import timereasoning.timeprop as timeprop

# 从两个单元素命题推出一个双元素命题的规则

class GetBeforeTimeP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.TemporalP, timeprop.TemporalP, timeprop.BeforeTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.TemporalP, prop2: timeprop.TemporalP) -> timeprop.BeforeTimeP | None:
        if not isinstance(prop1, (timeprop.TemporalP, timeprop.SubTemporalP)) or not isinstance(prop2, (timeprop.TemporalP, timeprop.SubTemporalP)):
            return None
        elif prop1.time < prop2.time:
            return super().reason(prop1, prop2)
        else:
            return None

class GetAfterTimeP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.TemporalP, timeprop.TemporalP, timeprop.AfterTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.TemporalP, prop2: timeprop.TemporalP) -> timeprop.AfterTimeP | None:
        if not isinstance(prop1, (timeprop.TemporalP, timeprop.SubTemporalP)) or not isinstance(prop2, (timeprop.TemporalP, timeprop.SubTemporalP)):
            return None
        elif prop1.time > prop2.time:
            return super().reason(prop1, prop2)
        else:
            return None

class GetSimultaneousP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.TemporalP, timeprop.TemporalP, timeprop.SimultaneousP)

    @classmethod
    def reason(cls, prop1: timeprop.TemporalP, prop2: timeprop.TemporalP) -> timeprop.SimultaneousP | None:
        if not isinstance(prop1, (timeprop.TemporalP, timeprop.SubTemporalP)) or not isinstance(prop2, (timeprop.TemporalP, timeprop.SubTemporalP)):
            return None
        elif prop1.time == prop2.time:
            return super().reason(prop1, prop2)
        else:
            return None

class GetLongTimeP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.DurationP, timeprop.DurationP, timeprop.LongTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.DurationP, prop2: timeprop.DurationP) -> timeprop.LongTimeP | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        elif prop1.duration > prop2.duration:
            return super().reason(prop1, prop2)
        else:
            return None

class GetShortTimeP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.DurationP, timeprop.DurationP, timeprop.ShortTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.DurationP, prop2: timeprop.DurationP) -> timeprop.ShortTimeP | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        elif prop1.duration < prop2.duration:
            return super().reason(prop1, prop2)
        else:
            return None

class GetSameLenTimeP(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.DurationP, timeprop.DurationP, timeprop.SameLenTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.DurationP, prop2: timeprop.DurationP) -> timeprop.SameLenTimeP | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        elif prop1.duration == prop2.duration:
            return super().reason(prop1, prop2)
        else:
            return None

# 传递性规则

class BeforeTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.BeforeP, timeprop.BeforeP, timeprop.BeforeP)

class BeforeTimeTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.BeforeTimeP, timeprop.BeforeTimeP, timeprop.BeforeTimeP)

class AfterTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.AfterP, timeprop.AfterP, timeprop.AfterP)

class AfterTimeTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.AfterTimeP, timeprop.AfterTimeP, timeprop.AfterTimeP)

class SimultaneousTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.SimultaneousP, timeprop.SimultaneousP, timeprop.SimultaneousP)

class LongTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.LongP, timeprop.LongP, timeprop.LongP)

class LongTimeTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.LongTimeP, timeprop.LongTimeP, timeprop.LongTimeP)

class ShortTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.ShortP, timeprop.ShortP, timeprop.ShortP)

class ShortTimeTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.ShortTimeP, timeprop.ShortTimeP, timeprop.ShortTimeP)

class SameLenTrans(rule.TransitivityRule):
    _rule_tuple = (timeprop.SameLenTimeP, timeprop.SameLenTimeP, timeprop.SameLenTimeP)

# 一单元素命题和一双元素命题推一单元素命题

class FromDoubleTime(rule.DoubleSingleToSingleRule):
    @classmethod
    def reason(cls, prop1: DoubleProp, prop2: SingleProp) -> SingleProp | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        if prop1.element1 == prop2.element:
            return timeprop.SingleTimeP.build(prop1.element2)
        elif prop1.element2 == prop2.element:
            return timeprop.SingleTimeP.build(prop1.element1)
        else:
            return None

class FromBeforeTime(FromDoubleTime):
    _rule_tuple = (timeprop.BeforeTimeP, timeprop.SingleTimeP, timeprop.SingleTimeP)

class FromAfterTime(FromDoubleTime):
    _rule_tuple = (timeprop.AfterTimeP, timeprop.SingleTimeP, timeprop.SingleTimeP)

class FromSimultaneous(FromDoubleTime):
    _rule_tuple = (timeprop.SimultaneousP, timeprop.SingleTimeP, timeprop.SingleTimeP)

class FromLongTime(FromDoubleTime):
    _rule_tuple = (timeprop.LongTimeP, timeprop.SingleTimeP, timeprop.SingleTimeP)

class FromShortTime(FromDoubleTime):
    _rule_tuple = (timeprop.ShortTimeP, timeprop.SingleTimeP, timeprop.SingleTimeP)

class FromSameLenTime(FromDoubleTime):
    _rule_tuple = (timeprop.SameLenTimeP, timeprop.SingleTimeP, timeprop.SingleTimeP)

# 增加推理规则：间隔+前后=具体时间前后
class BeforeandGap(rule.DoubleAdd):
    _rule_tuple = (timeprop.BeforeP, timeprop.GapTimeP, timeprop.BeforeTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.BeforeP, prop2: timeprop.GapTimeP) -> DoubleProp | None:
        new = super().reason(prop1, prop2)
        if new is None:
            return None
        else:
            new.diff = prop2.diff
            return new

class AfterandGap(rule.DoubleAdd):
    _rule_tuple = (timeprop.AfterP, timeprop.GapTimeP, timeprop.AfterTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.AfterP, prop2: timeprop.GapTimeP) -> DoubleProp | None:
        new = super().reason(prop1, prop2)
        if new is None:
            return None
        else:
            new.diff = prop2.diff
            return new

class TempBeforeDurative(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.TemporalP, timeprop.DurativeP, timeprop.BeforeP)

    @classmethod
    def reason(cls, prop1: timeprop.TemporalP, prop2: timeprop.DurativeP) -> DoubleProp | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        if prop1.time < prop2.time:
            return super().reason(prop1, prop2)
        else:
            return None

class TempAfterDurative(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.TemporalP, timeprop.DurativeP, timeprop.AfterP)

    @classmethod
    def reason(cls, prop1: timeprop.TemporalP, prop2: timeprop.DurativeP) -> DoubleProp | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        if prop1.time > prop2.endtime:
            return super().reason(prop1, prop2)
        else:
            return None

class GetDuring(rule.TwoSingleToDoubleRule):
    _rule_tuple = (timeprop.SingleTimeP, timeprop.DurativeP, timeprop.DuringTimeP)

    @classmethod
    def reason(cls, prop1: timeprop.SingleTimeP, prop2: timeprop.DurativeP) -> timeprop.DuringTimeP | None:
        if not cls._assert_condition(prop1, prop2):
            return None
        if isinstance(prop1, timeprop.TemporalP):
            if prop1.time >= prop2.time and prop1.time <= prop2.endtime:
                return super().reason(prop1, prop2)
        elif isinstance(prop1, timeprop.DurativeP):
            if prop1.time <= prop2.time and prop1.endtime <= prop2.endtime:
                return super().reason(prop1, prop2)
            elif prop1.time >= prop2.time and prop1.endtime >= prop2.endtime:
                return super().reason(prop1, prop2)
            elif prop1.time <= prop2.time and prop1.endtime >= prop2.endtime:
                return super().reason(prop1, prop2)
            elif prop1.time >= prop2.time and prop1.endtime <= prop2.endtime:
                return super().reason(prop1, prop2)
        return None

# 时间推理规则列表
RULES: list[type[rule.Rule]] = [
    GetBeforeTimeP,
    GetAfterTimeP,
    GetSimultaneousP,
    GetLongTimeP,
    GetShortTimeP,
    GetSameLenTimeP,
    BeforeTrans,
    BeforeTimeTrans,
    AfterTrans,
    AfterTimeTrans,
    SimultaneousTrans,
    LongTrans,
    LongTimeTrans,
    ShortTrans,
    ShortTimeTrans,
    SameLenTrans,
    FromBeforeTime,
    FromAfterTime,
    FromSimultaneous,
    FromLongTime,
    FromShortTime,
    FromSameLenTime,
    BeforeandGap,
    AfterandGap,
    # 增加时点-时段的前后推理规则
    # 1-9修改：移除时点-时段的前后推理规则
    # TempBeforeDurative,
    # TempAfterDurative,
    # 增加During推理规则
    GetDuring,
]
