# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
定义了时间中的事件类，作为时间推理的基本元素
"""

import abc
import random
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition.element import Element

class Event(Element):
    """表示一个事件"""
    @abc.abstractmethod
    def __init__(self, verb: str, object: str, time: int) -> None:
        """初始化事件

        Args:
            verb (str): 事件动词
            object (str): 事件宾语
            time (int): 事件发生时间
        """
        self.verb = verb
        self.object = object
        self.time = time
        self._alias: list[dict[str, str]] = [] # 事件的别名

    def event(self) -> str:
        """随机选择事件的陈述"""
        event_dict: dict[str, str] = random.choice(self._alias + [{"verb": self.verb, "object": self.object}])
        return f"{event_dict['verb']}{event_dict['object']}"

    def add_alias(self, verb: str, object: str) -> None:
        """添加事件的别名

        Args:
            verb (str): 事件动词
            object (str): 事件宾语
        """
        self._alias.append({'verb': verb, 'object': object})
    
    def __str__(self) -> str:
        """返回事件的初始描述

        Returns:
            str: 事件的描述
        """
        return f"{self.verb}{self.object}"
        
    def __eq__(self, other: object) -> bool:
        """判断两个事件是否相等，方法是检查两个事件的动词、宾语、时间、频率、结束事件等是否相等

        Args:
            value (object): 另一个事件

        Returns:
            bool: 两个事件是否相等
        """
        return super().__eq__(other) and self.verb == other.verb and self.object == other.object and self.time == other.time
    
    @classmethod
    def build_event(cls, verb: str, object: str, time: int, **kwargs) -> 'Event':
        """根据参数生成事件的工厂方法，根据参数生成不同类型的事件\n
        如果没有额外参数，则生成瞬时事件\n
        如果有frequency参数，则生成频率事件，且可以提供endtime参数\n
        如果有endtime参数，则生成持续事件\n
        否则抛出NotImplementedError

        Returns:
            Event: 生成的事件
        """
        if not kwargs: # 如果没有额外参数，则生成瞬时事件
            return TemporalEvent(verb, object, time)
        elif 'frequency' in kwargs: # 如果有frequency参数，则生成频率事件
            return FreqEvent(verb, object, time, kwargs['frequency'], kwargs.get('endtime', None))
        elif 'endtime' in kwargs: # 如果有endtime参数，则生成持续事件
            return DurativeEvent(verb, object, time, kwargs['endtime'])
        else:
            raise NotImplementedError(f"暂不支持按照额外参数{kwargs.keys()}生成事件")

class TemporalEvent(Event):
    """表示一个瞬时事件"""
    def __init__(self, verb: str, object: str, time: int) -> None:
        """初始化瞬时事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
            time (int): 事件发生时间
        """
        super().__init__(verb, object, time)

class SubEvent(TemporalEvent):
    """表示一个事件的子事件"""
    def __init__(self, verb: str, object: str, time: int, parent: Event) -> None:
        super().__init__(verb, object, time)
        self.parent: Event = parent

class Duration(Event):
    """表示一个持续事件的时长"""
    def __init__(self, verb: str, object: str, time: int, parent: Event) -> None:
        super().__init__(verb, object, time)
        self.parent: Event = parent

class DurativeEvent(Event):
    """表示一个持续事件"""
    def __init__(self, verb: str, object: str, time: int, endtime: int) -> None:
        """初始化持续事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
            time (int): 事件发生起始时间
            endtime (int): 事件结束时间
        """
        super().__init__(verb, object, time)
        self.endtime = endtime
        self.duration = self.endtime - self.time # 事件的持续时间
        self.start_event: SubEvent = SubEvent("开始", self.event, time, self) # 事件的开始事件
        self.end_event: SubEvent = SubEvent("结束", self.event, endtime, self) # 事件的结束事件
        self.duration_event: Duration = Duration(verb, object, self.duration, self) # 事件的持续时间事件

    def set_start_event(self, verb: str, object: str) -> None:
        """设置事件的开始事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
        """
        self.start_event = SubEvent(verb, object, self.time, self)

    def set_end_event(self, verb: str, object: str) -> None:
        """设置事件的结束事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
        """
        self.end_event = SubEvent(verb, object, self.endtime, self)

    def set_duration_event(self, verb: str, object: str) -> None:
        """设置事件的持续时间事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
        """
        self.duration_event = Duration(verb, object, self.duration, self)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.endtime == other.endtime
    
class FreqEvent(Event):
    """表示一个频率发生事件"""
    def __init__(self, verb: str, object: str, time: int, frequency: int, endtime: int) -> None:
        """初始化频率发生事件
        
        Args:
            verb (str): 事件动词
            object (str): 事件宾语
            time (int): 事件发生起始时间
            frequency (int): 事件频率
            endtime (int, optional): 事件结束时间.
        """
        super().__init__(verb, object, time)
        self.frequency = frequency
        self.endtime = endtime
        self.sub_events: list[SubEvent] = [SubEvent(verb, object, i, self) for i in range(time, endtime+1, frequency)] # 事件的子事件

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.frequency == other.frequency and self.endtime == other.endtime