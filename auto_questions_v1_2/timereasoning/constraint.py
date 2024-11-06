# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-04

"""
通过本模块定义的函数和类，定义并运用事件之间的约束关系
定义约束时，需要指定约束的类型
目前将事件处理成使用字符串表示，后续可以考虑使用对象表示
"""

import networkx as nx
import json5
import abc
import sys
from pathlib import Path
from typing import Any, Optional
import random

CEILING = "ceiling"
FLOOR = "floor"

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import event as ev

class Constraint(metaclass = abc.ABCMeta):
    """两个事件的约束关系
    """
    def __init__(self, main_event: str, std_event: str) -> None:
        self.main_event = main_event
        self.std_event = std_event

    @abc.abstractmethod
    def get(self) -> dict[str, int]:
        """获取约束关系决定的时间范围上界或下界"""
        pass

    @classmethod
    def build(cls, record: dict[str, Any]) -> "Constraint":
        """根据记录构建约束关系的工厂方法

        Args:
            record (dict[str, Any]): 记录

        Raises:
            ValueError: 记录具有未知的约束类型

        Returns:
            Constraint: 约束关系实例
        """
        typ: str = record["type"]
        param = {k: v for k, v in record.items() if k != "type"}
        if typ == "sametime":
            return SameTimeConstraint(**param)
        elif typ == "before":
            return BeforeConstraint(**param)
        elif typ == "after":
            return AfterConstraint(**param)
        elif typ == "minbefore":
            return MinimumBeforeConstraint(**param)
        elif typ == "minafter":
            return MinimumAfterConstraint(**param)
        elif typ == "maxbefore":
            return MaximumBeforeConstraint(**param)
        elif typ == "maxafter":
            return MaximumAfterConstraint(**param)
        elif typ == "certainbefore":
            return CertainBeforeConstraint(**param)
        elif typ == "certainafter":
            return CertainAfterConstraint(**param)
        elif typ == "rangetime":
            return RangeTimeConstraint(**param)
        else:
            raise ValueError(f"记录{record}具有未知的约束类型: {typ}")

class SameTimeConstraint(Constraint):
    """两个瞬时事件同时发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str) -> None:
        super().__init__(main_event, std_event)

    def get(self) -> dict[str, int]:
        return {CEILING: 0, FLOOR: 0}

class BeforeConstraint(Constraint):
    """第一个事件在第二个事件之前发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str) -> None:
        super().__init__(main_event, std_event)

    def get(self) -> dict[str, int]:
        return {CEILING: 0}

class AfterConstraint(Constraint):
    """第一个事件在第二个事件之后发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str) -> None:
        super().__init__(main_event, std_event)

    def get(self) -> dict[str, int]:
        return {FLOOR: 0}

class MinimumBeforeConstraint(Constraint):
    """第一个事件在第二个事件之前至少一段时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {CEILING: -self.time}

class MinimumAfterConstraint(Constraint):
    """第一个事件在第二个事件之后至少一段时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {FLOOR: self.time}

class MaximumBeforeConstraint(Constraint):
    """第一个事件在第二个事件之前最多一段时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {FLOOR: -self.time, CEILING: 0}

class MaximumAfterConstraint(Constraint):
    """第一个事件在第二个事件之后最多一段时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {FLOOR: 0, CEILING: self.time}

class CertainBeforeConstraint(Constraint):
    """第一个事件在第二个事件之前特定时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {FLOOR: -self.time, CEILING: -self.time}

class CertainAfterConstraint(Constraint):
    """第一个事件在第二个事件之后特定时间发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, time: int) -> None:
        super().__init__(main_event, std_event)
        self.time = time

    def get(self) -> dict[str, int]:
        return {FLOOR: self.time, CEILING: self.time}

class RangeTimeConstraint(Constraint):
    """第一个事件在第二个事件之后特定时间范围内发生的约束关系
    """
    def __init__(self, main_event: str, std_event: str, floor: int, ceiling: int) -> None:
        """初始化约束关系，表示第一个事件在第二个事件之后特定时间范围内发生

        Args:
            main_event (str): 主要事件
            std_event (str): 基准事件
            floor (int): 下界
            ceiling (int): 上界
        """
        super().__init__(main_event, std_event)
        assert floor <= ceiling
        self.floor = floor
        self.ceiling = ceiling

    def get(self) -> dict[str, int]:
        return {FLOOR: self.floor, CEILING: self.ceiling}

# TODO: 目前的约束文件需要尝试性书写（有些写法虽然同义，但是会报错）
# 需要调整约束器的设计
# 一种可能的思路是使用拓扑排序，然后按照逆序确定事件的约束情况和事件
class ConstraintMachine:
    def __init__(self, lower_bound: int, upper_bound: int) -> None:
        self.events: list[ev.Event] = []
        self.constraints_graph: nx.DiGraph = None
        assert lower_bound <= upper_bound, "下界应小于等于上界"
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def add_event(self, *events: ev.Event) -> None:
        """向约束器中添加事件

        Args:
            *events (ev.Event): 事件
        """
        self.events.extend(events)

    def read_constraints(self, file: str | Path) -> None:
        """读取约束关系

        Args:
            constraints (list[dict[str, Any]]): 约束关系
        """
        self.constraints_graph = nx.DiGraph()
        with open(file, "r", encoding="utf-8") as f:
            records: list[dict[str, Any]] = json5.load(f)
        for record in records:
            constraint = Constraint.build(record)
            self.constraints_graph.add_edge(record["std_event"], record["main_event"], constraint=constraint)
        if not nx.is_directed_acyclic_graph(self.constraints_graph):
            raise ValueError("约束图中存在环")
        else:
            print("约束图构建成功.")

    def _check_event(self, name: str) -> Optional[ev.Event]:
        """检查事件是否存在，如果存在则返回事件，否则返回None

        Args:
            name (str): 事件名称

        Returns:
            Optional[ev.Event]: 事件，如果不存在则返回None
        """
        for event in self.events:
            if type(event) == ev.TemporalEvent and str(event) == name:
                return event
            elif type(event) == ev.DurativeEvent:
                if str(event) == name:
                    return event
                elif str(event.start_event) == name:
                    return event.start_event
                elif str(event.end_event) == name:
                    return event.end_event
    
    def _random_time(self, event_name: str) -> int:
        """返回事件的随机时间

        Args:
            event_name (str): 事件名称

        Returns:
            int: 事件的随机时间
        """
        constraints = self.constraints_graph.in_edges(event_name, data=True)
        floor, ceiling = self.lower_bound, self.upper_bound # 初始化时间下限和上限
        for std_event, _, data in constraints:
            std = self._check_event(std_event)
            if std is None:
                std_time = self._random_time(std_event)
            elif std.time is None:
                new_std = self._set_time(std)
                std_time = new_std.time
            else:
                std_time = std.time
            constraint: Constraint = data["constraint"]
            constraint_info = constraint.get()
            # 更新时间下限和上限
            # 更新时间下限
            new_floor = constraint_info.get(FLOOR, None)
            # 如果存在新的下限，则取最大值
            if new_floor is not None:
                floor = max(floor, new_floor + std_time)
            # 更新时间上限
            new_ceiling = constraint_info.get(CEILING, None)
            # 如果存在新的上限，则取最小值
            if new_ceiling is not None:
                ceiling = min(ceiling, new_ceiling + std_time)
        if floor > ceiling:
            raise ValueError(f"事件{event_name}的时间下限{floor}大于上限{ceiling}")
        return random.randint(floor, ceiling) # 生成随机时间

    def _set_time(self, event: ev.TemporalEvent) -> ev.TemporalEvent:
        """为事件设置时间

        Args:
            event (ev.TemporalEvent): 事件

        Returns:
            ev.TemporalEvent: 设置时间后的事件
        """
        # 如果已经定好时间就无需约束
        if event.time is not None:
            return event
        # 否则使用约束图进行约束
        constraints = list(self.constraints_graph.in_edges(str(event), data=True))
        # print(constraints)
        if len(constraints) == 0:
            event.time = self.lower_bound
            return event

        # 生成随机时间
        event.time = self._random_time(str(event))
        return event
    
    def run(self) -> list[ev.Event]:
        """运行约束器，为事件随机生成时间信息后返回

        Returns:
            list[ev.Event]: 事件列表
        """
        for event in self.events:
            if type(event) == ev.TemporalEvent:
                new_event = self._set_time(event)
            elif type(event) == ev.DurativeEvent:
                # 自动向图形中添加约束
                new_start_event = self._set_time(event.start_event)
                new_end_event = self._set_time(event.end_event)
                event.time = new_start_event.time
                event.endtime = new_end_event.time
                event.duration = new_end_event.time - new_start_event.time
                event.duration_event.time = event.duration
                new_event = event
        for event in self.events:
            if type(event) == ev.TemporalEvent:
                print(f"{str(event)}: {event.time}")
            elif type(event) == ev.DurativeEvent:
                print(f"{str(event)}: {event.time}, {event.endtime}, {event.duration}")
        return self.events