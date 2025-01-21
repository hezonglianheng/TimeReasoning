# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
关于时间命题的基本定义和基本操作
"""

import json5
import sys
from typing import Optional, Union
from pathlib import Path
import abc

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop
import timereasoning.event as event
import timereasoning.config as config

class TimeP(prop.Proposition):
    """表示一个时间命题"""
    @abc.abstractmethod
    def __init__(self, askable: bool = False, precise: bool = True):
        """初始化时间命题

        Args:
            askable (bool, optional): 是否可询问. 默认为False.
            precise (bool, optional): 是否精确. 默认为True.
        """
        super().__init__(askable, precise)
        # 1-21新增：通过函数读取命题的难度
        self.difficulty = self._get_difficulty()

    def _get_difficulty(self) -> int:
        """获取时间命题的难度

        Returns:
            int: 时间命题的难度
        """
        # 读取难度配置文件
        with config.PROP_DIFFICULTY_PATH.open("r", encoding="utf-8") as f:
            difficulty_dict: dict[str, int] = json5.load(f)
        # 根据模板关键词获取难度，默认值为1
        return difficulty_dict.get(self.temp_key, 1)

# 单事件时间命题
class SingleTimeP(prop.SingleProp, TimeP):
    """表示一个具有单个事件的时间命题"""
    def __init__(self, element: event.Event, askable: bool = True, precise: bool = True):
        """初始化一个具有单个事件的时间命题

        Args:
            element (event.Event): 事件
            askable (bool, optional): 是否可询问. 默认为True.
            precise (bool, optional): 是否精确. 默认为True.
        """
        super().__init__(element, askable, precise)
        self.time = element.time
        self.child_props: list["SubTemporalP" | "DurationP"] = []

    def attrs(self) -> dict[str, str]:
        res = super().attrs()
        if isinstance(self.element, event.Event):
            # res |= {"element": self.element.event()}
            res |= {"element": str(self.element)}
        return res

    @classmethod
    def build(cls, element: event.Event, askable: bool = True) -> 'SingleTimeP':
        """根据事件生成时间命题的工厂方法

        Args:
            element (event.Event): 事件
            askable (bool, optional): 是否可询问. 默认为True.

        Returns:
            SingleTimeP: 生成的时间命题

        Raises:
            NotImplementedError: 暂不支持按照element的类型生成时间命题
        """
        if isinstance(element, event.SubEvent):
            return SubTemporalP(element, askable)
        elif isinstance(element, event.TemporalEvent):
            return TemporalP(element, askable)
        elif isinstance(element, event.DurativeEvent):
            return DurativeP(element, askable)
        elif isinstance(element, event.FreqEvent):
            return FreqP(element, askable)
        elif isinstance(element, event.Duration):
            return DurationP(element, askable)
        else:
            raise NotImplementedError(f"暂不支持按照{type(element)}生成时间命题")

    def get_child_props(self) -> list[Union["SubTemporalP", "DurationP"]]:
        """返回时间命题的子命题

        Returns:
            list[TemporalP | DurationP]: 时间命题的子命题
        """
        return self.child_props

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.time == other.time

class TemporalP(SingleTimeP):
    """表示一个时间点的命题"""
    def __init__(self, element: event.TemporalEvent, askable: bool = True):
        super().__init__(element, askable)
    
    @property
    def temp_key(self) -> str:
        """返回时间点命题的模板关键词，为str"""
        return "temporal"
    
    def __eq__(self, other: object) -> bool:
        if super().__eq__(other):
            return True
        elif isinstance(self, TemporalP) and isinstance(other, TemporalP):
            return self.element == other.element and self.time == other.time

    @property
    def typetag(self) -> str:
        return "时刻-具体值"

class SubTemporalP(TemporalP):
    """
    表示一个时间点的命题，其是另一个时间命题的子命题\n
    例如：亲命题为“从2000年到2010年，小明当老师”，则其中一个子命题为“2004年，小明正在当老师”\n
    其执行逻辑基本与TemporalP相同
    """
    def __init__(self, element: event.SubEvent, askable: bool = True):
        super().__init__(element, askable)
        self.parent = element.parent

class DurationP(SingleTimeP):
    """表示时间段时长的命题"""
    def __init__(self, element: event.Duration, askable: bool = True):
        super().__init__(element, askable)
        self.parent = element.parent
        self.duration = element.time
        self.related_prop: list[BeforeTimeP] = []

    @property
    def temp_key(self) -> str:
        return "duration"

    def add_related_prop(self, prop: "BeforeTimeP") -> None:
        """增加关联事件，将时间段时长的命题和时间点先后顺序的命题关联起来

        Args:
            prop (BeforeTimeP): 时间点先后顺序的命题
        """
        self.related_prop.append(prop)

    def contained(self, prop_list: list[prop.Proposition]) -> bool:
        return super().contained(prop_list) or self.related_prop[0].contained(prop_list)

    @property
    def typetag(self) -> str:
        return "时长-具体值"
    
class DurativeP(SingleTimeP):
    """表示一个时间段的命题"""
    def __init__(self, element: event.DurativeEvent, askable: bool = True):
        super().__init__(element, askable)
        self.endtime = element.endtime
        self.duration = element.duration
        # 10-30修订：子事件和母事件具有相同的可提问性
        self.start_p = SubTemporalP(element.start_event, askable)
        self.end_p = SubTemporalP(element.end_event, askable)
        self.duration_p = DurationP(element.duration_event, askable)
        self.duration_p.add_related_prop(BeforeTimeP(element.start_event, element.end_event))
        self.child_props = [self.start_p, self.end_p, self.duration_p]

    @property
    def num_of_conditions(self) -> int:
        return 2
    
    @property
    def temp_key(self) -> str:
        return "durative"
    
    def get_child_props(self) -> list[SubTemporalP | DurationP]:
        # 将时间段的开始和结束时间点及时长事件加入到子命题中
        return super().get_child_props()
    
    def contained(self, prop_list: list[prop.Proposition]) -> bool:
        contain_self =  super().contained(prop_list)
        if contain_self:
            return contain_self
        else:
            # 如果时间段的开始和结束时间点及时长事件至少2个包含在命题列表中，则返回True
            child_contained = [i.contained(prop_list) for i in self.child_props]
            if sum(child_contained) >= 2:
                return True
            else:
                return False

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value) and self.endtime == value.endtime and self.duration == value.duration
    
    @property
    def typetag(self) -> str:
        return "时段-具体值"

class FreqP(SingleTimeP):
    """表示一个时间频率的命题"""
    def __init__(self, element: event.FreqEvent, askable: bool = True):
        super().__init__(element, askable)
        self.frequency = element.frequency
        self.endtime = element.endtime
        self.child_props = [SubTemporalP(i) for i in element.sub_events]

    @property
    def num_of_conditions(self) -> int:
        return len(self.child_props)

    @property
    def temp_key(self) -> str:
        return "freq"
    
    def get_child_props(self) -> list[SubTemporalP]:
        return super().get_child_props()
    
    def contained(self, prop_list: list[prop.Proposition]) -> bool:
        contain_self =  super().contained(prop_list)
        if contain_self:
            return contain_self
        else:
            return all([i.contained(prop_list) for i in self.child_props])

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.frequency == other.frequency and self.endtime == other.endtime

    @property
    def typetag(self) -> str:
        return "时频-具体值"

# 双事件时间命题
class DoubleTimeP(prop.DoubleProp, TimeP):
    """表示一个具有两个事件的时间命题"""
    def __init__(self, element1: event.Event, element2: event.Event, askable: bool = False, precise: bool = True):
        """初始化一个具有两个事件的时间命题

        Args:
            element1 (event.Event): 命题中被描述相对情形的事件
            element2 (event.Event): 命题中的参照事件
            askable (bool, optional): 是否可询问. 默认为False.
            precise (bool, optional): 是否精确. 默认为True.
        """
        super().__init__(element1, element2, askable, precise)
        # 1-21移除：移除二元命题的默认难度
        # self.difficulty = 2 # 1-15新增：二元时间命题的默认难度为2
        
    def attrs(self) -> dict[str, str]:
        res = super().attrs()
        if isinstance(self.element1, event.Event):
            # res |= {"element1": self.element1.event()}
            res |= {"element1": str(self.element1)}
        if isinstance(self.element2, event.Event):
            # res |= {"element2": self.element2.event()}
            res |= {"element2": str(self.element2)}
        return res
    
    @classmethod
    def build(cls, element1: event.Event, element2: event.Event) -> Optional["DoubleTimeP"]:
        """根据事件生成时间命题的工厂方法

        Args:
            new_element (event.Event): 命题中被描述相对情形的事件
            prev_element (event.Event): 命题中的参照事件

        Raises:
            NotImplementedError: 两个事件的类型不符，无法生成时抛出

        Returns:
            Optional[DoubleTimeP]: 生成的命题
        """
        param_dict = {"element1": element1, "element2": element2}
        if all([isinstance(i, event.TemporalEvent) for i in param_dict.values()]):
            if element1.time > element2.time:
                return AfterTimeP(**param_dict)
            elif element1.time < element2.time:
                return BeforeTimeP(**param_dict)
            else:
                return SimultaneousP(**param_dict)
        elif all([isinstance(i, event.Duration) for i in param_dict.values()]):
            if element1.time > element2.time:
                return LongTimeP(**param_dict)
            elif element1.time < element2.time:
                return ShortTimeP(**param_dict)
            else:
                return SameLenTimeP(**param_dict)
        else:
            return None

class BeforeP(DoubleTimeP):
    """表示一个事件发生在另一个事件之前的时间命题，是非精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.Event, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.precise = False

    @property
    def temp_key(self) -> str:
        return "before"

    @property
    def typetag(self) -> str:
        return "时刻-定性比较"
    
class BeforeTimeP(DoubleTimeP):
    """表示一个时间点发生在另一个时间点之前特定时间的时间命题，是精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.TemporalEvent, askable: bool = True):
        super().__init__(element1, element2, askable)
        # self.diff = abs(element2.time - element1.time)
        self.diff = element2.time - element1.time

    @property
    def temp_key(self) -> str:
        return "before_time"
    
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.diff == other.diff
    
    @property
    def typetag(self) -> str:
        return "时刻-定量比较"
    
class AfterP(DoubleTimeP):
    """表示一个事件发生在另一个事件之后的时间命题，是非精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.Event, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.precise = False

    @property
    def temp_key(self) -> str:
        return "after"

    @property
    def typetag(self) -> str:
        return "时刻-定性比较"
    
class AfterTimeP(DoubleTimeP):
    """表示一个时间点发生在另一个时间点之后特定时间的时间命题，是精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.TemporalEvent, askable: bool = True):
        super().__init__(element1, element2, askable)
        # self.diff = abs(element1.time - element2.time)
        self.diff = element1.time - element2.time

    @property
    def temp_key(self) -> str:
        return "after_time"
    
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.diff == other.diff
    
    @property
    def typetag(self) -> str:
        return "时刻-定量比较"
    
class SimultaneousP(DoubleTimeP):
    """表示两个事件同时发生的时间命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.TemporalEvent, askable: bool = True):
        super().__init__(element1, element2, askable)

    @property
    def temp_key(self) -> str:
        return "simultaneous"
    
    @property
    def typetag(self) -> str:
        return "时刻-定性比较"
    
class GapTimeP(DoubleTimeP):
    """表示两个事件之间的具体时间间隔的时间命题，是非精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.TemporalEvent, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.diff = abs(element1.time - element2.time)
        self.precise = False
        # 1-21修改：移除时间间隔的默认难度
        # self.difficulty = 3 # 1-15新增：时间间隔的默认难度为3

    @property
    def temp_key(self) -> str:
        return "gap_time"

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.diff == other.diff
    
    @property
    def typetag(self) -> str:
        return "时刻-定量间隔"
    
class LongP(DoubleTimeP):
    """表示某持续事件的时长长于另一持续事件的时间命题，是非精确命题"""
    def __init__(self, element1: event.Duration, element2: event.Duration, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.precise = False

    @property
    def temp_key(self) -> str:
        return "long"

    @property
    def typetag(self) -> str:
        return "时长-定性比较"
    
class LongTimeP(DoubleTimeP):
    """表示某持续事件的时长长于另一持续事件具体时长的时间命题，是精确命题"""
    def __init__(self, element1: event.Duration, element2: event.Duration, askable: bool = True):
        super().__init__(element1, element2, askable)
        # self.diff = abs(element1.time - element2.time)
        self.diff = element1.time - element2.time

    @property
    def temp_key(self) -> str:
        return "long_time"
    
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.diff == other.diff
    
    @property
    def typetag(self) -> str:
        return "时长-定量比较"
    
class ShortP(DoubleTimeP):
    """表示某持续事件的时长短于另一持续事件的时间命题，是非精确命题"""
    def __init__(self, element1: event.Duration, element2: event.Duration, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.precise = False

    @property
    def temp_key(self) -> str:
        return "short"
    
    @property
    def typetag(self) -> str:
        return "时长-定性比较"
    
class ShortTimeP(DoubleTimeP):
    """表示某持续事件的时长短于另一持续事件具体时长的时间命题，是精确命题"""
    def __init__(self, element1: event.Duration, element2: event.Duration, askable: bool = True):
        super().__init__(element1, element2, askable)
        # self.diff = abs(element1.time - element2.time)
        self.diff = element2.time - element1.time

    @property
    def temp_key(self) -> str:
        return "short_time"

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.diff == other.diff
    
    @property
    def typetag(self) -> str:
        return "时长-定量比较"
    
class SameLenTimeP(DoubleTimeP):
    """表示两个持续事件具有相同时长的时间命题，是精确命题"""
    def __init__(self, element1: event.Duration, element2: event.Duration, askable: bool = True):
        super().__init__(element1, element2, askable)

    @property
    def temp_key(self) -> str:
        return "same_len"

    @property
    def typetag(self) -> str:
        return "时长-定性比较"

class DuringTimeP(DoubleTimeP):
    """表示一个事件发生在另一个持续事件的时间命题，是非精确命题"""
    def __init__(self, element1: event.TemporalEvent, element2: event.DurativeEvent, askable: bool = True):
        super().__init__(element1, element2, askable)
        self.precise = False

    @property
    def temp_key(self) -> str:
        return "during"

    @property
    def typetag(self) -> str:
        return "时刻-定性比较"