# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
关于时间命题的基本定义和基本操作
"""

import sys
from typing import Self, Optional
from pathlib import Path
import abc

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop
import timereasoning.event as event

class TimeP(prop.Proposition):
    """表示一个时间命题"""
    @abc.abstractmethod
    def __init__(self, symmetrical: bool = False, precise: bool = False, askable: bool = False):
        """初始化时间命题

        Args:
            symmetrical (bool, optional): 是否对称. 默认为False.
            precise (bool, optional): 是否精确. 默认为False.
            askable (bool, optional): 是否可询问. 默认为False.
        """
        super().__init__(symmetrical, precise, askable)

# 单事件时间命题
class SingleTimeP(TimeP):
    """表示一个具有单个事件的时间命题"""
    def __init__(self, element: event.Event, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        """初始化一个具有单个事件的时间命题

        Args:
            element (event.Event): 事件
            symmetrical (bool, optional): 是否对称. 默认为True.
            precise (bool, optional): 是否精确. 默认为True.
            askable (bool, optional): 是否可询问. 默认为True.
        """        
        super().__init__(symmetrical, precise, askable)
        self.element = element
        self.time = element.time
        self.child_props: list[SubTemporalP] = []

    def attrs(self) -> dict[str, str]:
        return super().attrs() | {"element": self.element.event()}

    @classmethod
    def build(cls, element: event.Event, symmetrical: bool = True, precise: bool = True, askable: bool = True) -> 'SingleTimeP':
        """根据事件生成时间命题的工厂方法

        Args:
            element (event.Event): 事件
            symmetrical (bool, optional): 是否对称. 默认为True.
            precise (bool, optional): 是否精确. 默认为True.
            askable (bool, optional): 是否可询问. 默认为True.

        Returns:
            SingleTimeP: 生成的时间命题

        Raises:
            NotImplementedError: 暂不支持按照element的类型生成时间命题
        """
        if isinstance(element, event.SubEvent):
            return SubTemporalP(element)
        elif isinstance(element, event.TemporalEvent):
            return TemporalP(element)
        elif isinstance(element, event.DurativeEvent):
            return DurativeP(element)
        elif isinstance(element, event.FreqEvent):
            return FreqP(element)
        elif isinstance(element, event.Duration):
            return DurationP(element)
        else:
            raise NotImplementedError(f"暂不支持按照{type(element)}生成时间命题")

    def get_child_props(self) -> list["SubTemporalP"]:
        """返回时间命题的子命题

        Returns:
            list[SubTemporalP]: 时间命题的子命题
        """
        return self.child_props

class TemporalP(SingleTimeP):
    """表示一个时间点的命题"""
    def __init__(self, element: event.TemporalEvent, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(element, symmetrical, precise, askable)
    
    @property
    def temp_key(self) -> str:
        """返回时间点命题的模板关键词，为str"""
        return "temporal"
    
class SubTemporalP(TemporalP):
    """
    表示一个时间点的命题，其是另一个时间命题的子命题\n
    例如：亲命题为“从2000年到2010年，小明当老师”，则其中一个子命题为“2004年，小明正在当老师”\n
    其执行逻辑基本与TemporalP相同
    """
    def __init__(self, element: event.SubEvent, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(element, symmetrical, precise, askable)
        self.parent_event = element.parent

class DurationP(SingleTimeP):
    """表示时间段时长的命题"""
    def __init__(self, element: event.Duration, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(element, symmetrical, precise, askable)
        self.parent_event = element.parent
        self.duration = element.time

    @property
    def temp_key(self) -> str:
        return "duration"
    
class DurativeP(SingleTimeP):
    """表示一个时间段的命题"""
    def __init__(self, element: event.DurativeEvent, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(element, symmetrical, precise, askable)
        self.endtime = element.endtime
        self.duration = element.duration
        self.start_p = SubTemporalP(element.start_event)
        self.end_p = SubTemporalP(element.end_event)
        self.duration_p = DurationP(element.duration_event)
        self.child_props = [self.start_p, self.end_p, self.duration_p]

    @property
    def temp_key(self) -> str:
        return "durative"
    
    def get_child_props(self) -> list[SubTemporalP | DurationP]:
        # 将时间段的开始和结束时间点及时长事件加入到子命题中
        return super().get_child_props()

    def got(self, prop_list: list[prop.Proposition]) -> bool:
        # 判断时间段的开始和结束时间点及时长事件是否包含在一个命题列表中
        got_self = super().got(prop_list)
        if got_self:
            return got_self
        else:
            got_child = [i.got(prop_list) for i in self.child_props]
            if sum(got_child) > 2:
                return True
            else:
                return False

class FreqP(SingleTimeP):
    """表示一个时间频率的命题"""
    def __init__(self, element: event.FreqEvent, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(element, symmetrical, precise, askable)
        self.frequency = element.frequency
        self.endtime = element.endtime
        self.child_props = [SubTemporalP(i) for i in element.sub_events]

    @property
    def temp_key(self) -> str:
        return "freq"
    
    def get_child_props(self) -> list[SubTemporalP]:
        return super().get_child_props()
    
    def got(self, prop_list: list[prop.Proposition]) -> bool:
        return super().got(prop_list) or all([i.got(prop_list) for i in self.child_props])

# 双事件时间命题
class DoubleTimeP(TimeP):
    """表示一个具有两个事件的时间命题"""
    def __init__(self, new_element: event.Event, prev_element: event.Event, symmetrical: bool = False, precise: bool = False, askable: bool = False):
        """初始化一个具有两个事件的时间命题

        Args:
            new_element (event.Event): 命题中被描述相对情形的事件
            prev_element (event.Event): 命题中的参照事件
            symmetrical (bool, optional): 是否对称. 默认为False.
            precise (bool, optional): 是否精确. 默认为False.
            askable (bool, optional): 是否可询问. 默认为False.
        """
        super().__init__(symmetrical, precise, askable)
        self.prev_element = prev_element
        self.new_element = new_element

    def swap(self) -> Optional[Self]:
        """若时间命题对称，则交换两个事件的位置得到新的时间命题。否则返回None

        Returns:
            Optional[Self]: 交换后的新时间命题或者None
        """
        if self.symmetrical: # 如果是对称的时间命题，则可以交换两个事件的位置
            return self.__class__(self.prev_element, self.new_element, self.symmetrical, self.precise, self.askable)
        else: # 否则返回None
            return None
        
    def attrs(self) -> dict[str, str]:
        return super().attrs() | {"new_element": self.new_element.event(), "prev_element": self.prev_element.event()}
    
    @classmethod
    def build(cls, new_element: event.Event, prev_element: event.Event) -> Optional["DoubleTimeP"]:
        """根据事件生成时间命题的工厂方法

        Args:
            new_element (event.Event): 命题中被描述相对情形的事件
            prev_element (event.Event): 命题中的参照事件

        Raises:
            NotImplementedError: 两个事件的类型不符，无法生成时抛出

        Returns:
            Optional[DoubleTimeP]: 生成的命题
        """
        param_dict = {"new_element": new_element, "prev_element": prev_element}
        if all([isinstance(i, event.TemporalEvent) for i in param_dict.values()]):
            if new_element.time > prev_element.time:
                return AfterTimeP(**param_dict)
            elif new_element.time < prev_element.time:
                return BeforeTimeP(**param_dict)
            else:
                return SimultaneousP(**param_dict)
        elif all([isinstance(i, event.Duration) for i in param_dict.values()]):
            if new_element.time > prev_element.time:
                return LongTimeP(**param_dict)
            elif new_element.time < prev_element.time:
                return ShortTimeP(**param_dict)
            else:
                return SameLenTimeP(**param_dict)
        else:
            return None

class BeforeP(DoubleTimeP):
    """表示一个事件发生在另一个事件之前的时间命题，是非精确命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = False, precise: bool = False, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "before"
    
class BeforeTimeP(DoubleTimeP):
    """表示一个时间点发生在另一个时间点之前特定时间的时间命题，是精确命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = False, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)
        self.diff = abs(prev_element.time - new_element.time)

    @property
    def temp_key(self) -> str:
        return "before_time"
    
class AfterP(DoubleTimeP):
    """表示一个事件发生在另一个事件之后的时间命题，是非精确命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = False, precise: bool = False, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "after"
    
class AfterTimeP(DoubleTimeP):
    """表示一个时间点发生在另一个时间点之后特定时间的时间命题，是精确命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = False, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)
        self.diff = abs(new_element.time - prev_element.time)

    @property
    def temp_key(self) -> str:
        return "after_time"
    
class SimultaneousP(DoubleTimeP):
    """表示两个事件同时发生的时间命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "simultaneous"
    
class GapTimeP(DoubleTimeP):
    """表示两个事件之间的具体时间间隔的时间命题，是非精确命题"""
    def __init__(self, new_element: event.TemporalEvent, prev_element: event.TemporalEvent, symmetrical: bool = True, precise: bool = False, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)
        self.diff = abs(new_element.time - prev_element.time)

    @property
    def temp_key(self) -> str:
        return "gap_time"
    
class LongP(DoubleTimeP):
    """表示某持续事件的时长长于另一持续事件的时间命题，是非精确命题"""
    def __init__(self, new_element: event.Duration, prev_element: event.Duration, symmetrical: bool = False, precise: bool = False, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "long"
    
class LongTimeP(DoubleTimeP):
    """表示某持续事件的时长长于另一持续事件具体时长的时间命题，是精确命题"""
    def __init__(self, new_element: event.Duration, prev_element: event.Duration, symmetrical: bool = False, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)
        self.diff = abs(new_element.time - prev_element.time)

    @property
    def temp_key(self) -> str:
        return "long_time"
    
class ShortP(DoubleTimeP):
    """表示某持续事件的时长短于另一持续事件的时间命题，是非精确命题"""
    def __init__(self, new_element: event.Duration, prev_element: event.Duration, symmetrical: bool = False, precise: bool = False, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "short"
    
class ShortTimeP(DoubleTimeP):
    """表示某持续事件的时长短于另一持续事件具体时长的时间命题，是精确命题"""
    def __init__(self, new_element: event.Duration, prev_element: event.Duration, symmetrical: bool = False, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)
        self.diff = abs(new_element.time - prev_element.time)

    @property
    def temp_key(self) -> str:
        return "short_time"
    
class SameLenTimeP(DoubleTimeP):
    """表示两个持续事件具有相同时长的时间命题，是精确命题"""
    def __init__(self, new_element: event.Duration, prev_element: event.Duration, symmetrical: bool = True, precise: bool = True, askable: bool = True):
        super().__init__(new_element, prev_element, symmetrical, precise, askable)

    @property
    def temp_key(self) -> str:
        return "same_len"
