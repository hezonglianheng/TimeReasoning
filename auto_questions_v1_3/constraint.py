# encoding: utf8
# date: 2025-02-23

"""根据输入文件中的约束关系，为事件获得满足约束的时间值
"""

import element
import represent
import event
import proposition as prop
import networkx as nx
from collections.abc import Sequence
from typing import Optional, Any
import random
import copy

# constants.
MAIN_EVENT = "main_event"
STD_EVENT = "std_event"
CONSTRAINT_TYPE = "constraint_type"
FLOOR = "floor"
CEILING = "ceiling"
CONSTRAINT = "constraint"
TIME = "time"
# 约束类型
BEFORE = "before"
AFTER = "after"
SIMULTANEOUS = "simultaneous"

class Constraint(element.Element):
    """约束类
    """
    def __init__(self, name = "", kind = "", **kwargs):
        constraint_dict = dict()
        floor_dict: Optional[dict] = kwargs.get(FLOOR)
        ceiling_dict: Optional[dict] = kwargs.get(CEILING)
        time_dict: Optional[dict] = kwargs.get(TIME) # 如果约束的floor和ceiling相等，则允许一种简写方式
        if time_dict:
            constraint_dict[FLOOR] = represent.CustomTimeDelta(**time_dict)
            constraint_dict[CEILING] = represent.CustomTimeDelta(**time_dict)
        if floor_dict:
            constraint_dict[FLOOR] = represent.CustomTimeDelta(**floor_dict)
        if ceiling_dict:
            constraint_dict[CEILING] = represent.CustomTimeDelta(**ceiling_dict)
        super().__init__(name, kwargs[CONSTRAINT_TYPE], **constraint_dict)

    def forward_update(self, main_times: dict[str, represent.CustomTime], std_times: dict[str, represent.CustomTime]) -> dict[str, represent.CustomTime]:
        """前向传播时，根据约束关系更新事件时间上下限

        Args:
            main_times (dict[str, represent.CustomTime]): 主要事件的时间范围
            std_times (dict[str, represent.CustomTime]): 参考事件的时间范围

        Returns:
            dict[str, represent.CustomTime]: 更新后的事件时间范围
        """
        std_floor = std_times[FLOOR]
        std_ceiling = std_times[CEILING]
        if self.kind == BEFORE:
            if self.has_attr(FLOOR):
                std_ceiling: represent.CustomTime = std_ceiling - self[FLOOR]
            if self.has_attr(CEILING):
                std_floor: represent.CustomTime = std_floor - self[CEILING]
        elif self.kind == AFTER:
            if self.has_attr(FLOOR):
                std_floor: represent.CustomTime = std_floor + self[FLOOR]
            if self.has_attr(CEILING):
                std_ceiling: represent.CustomTime = std_ceiling + self[CEILING]
        new_floor = max(std_floor, main_times[FLOOR])
        new_ceiling = min(std_ceiling, main_times[CEILING])
        return {FLOOR: new_floor, CEILING: new_ceiling}

    def backward_update(self, main_time: represent.CustomTime, std_times: dict[str, represent.CustomTime]) -> dict[str, represent.CustomTime]:
        """后向传播时，根据约束关系获得新的事件时间值范围

        Args:
            main_time (represent.CustomTime): 主要事件的时间值
            std_times (dict[str, represent.CustomTime]): 参考事件的时间范围

        Raises:
            ValueError: 约束类型不合法

        Returns:
            dict[str, represent.CustomTime]: 新的事件时间值范围
        """
        std_floor = std_times[FLOOR]
        std_ceiling = std_times[CEILING]
        if self.kind == BEFORE:
            if self.has_attr(FLOOR):
                std_floor: represent.CustomTime = main_time + self[FLOOR]
            if self.has_attr(CEILING):
                std_ceiling: represent.CustomTime = main_time + self[CEILING]
        elif self.kind == AFTER:
            if self.has_attr(FLOOR):
                std_floor: represent.CustomTime = main_time - self[CEILING]
            if self.has_attr(CEILING):
                std_ceiling: represent.CustomTime = main_time - self[FLOOR]
        elif self.kind == SIMULTANEOUS:
            assert std_floor <= main_time <= std_ceiling, "参考事件时间范围不包含主要事件时间"
            # 直接将参考时间设置为主要事件时间范围
            std_floor = copy.deepcopy(main_time)
            std_ceiling = copy.deepcopy(main_time)
        else:
            raise ValueError(f"不支持的约束类型{self.kind}")
        assert std_floor <= std_ceiling, "时间范围不合法"
        return {FLOOR: std_floor, CEILING: std_ceiling}

class ConstraintMachine:
    def __init__(self, event_names: Sequence[str], constraint_rules: Sequence[dict], upper_bound: represent.CustomTime, lower_bound: represent.CustomTime):
        self.event_names = event_names
        self.constraint_rules = constraint_rules
        assert upper_bound > lower_bound, "约束机类中上界应大于下界"
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.constraint_graph = nx.DiGraph()
        self._construct()
        self._forward()

    def _construct(self):
        """根据输入构造约束图
        """
        # 设置约束图中的节点
        for name in self.event_names:
            self.constraint_graph.add_node(name, **{FLOOR: self.lower_bound, CEILING: self.upper_bound})
        # 设置约束图中的边
        for rule in self.constraint_rules:
            constraint = Constraint(**rule)
            self.constraint_graph.add_edge(rule[STD_EVENT], rule[MAIN_EVENT], CONSTRAINT = constraint)
        # 检查约束图是否有环
        if not nx.is_directed_acyclic_graph(self.constraint_graph):
            cycle = nx.find_cycle(self.constraint_graph, orientation = "original")
            cycle_string = " -> ".join([edge[0] for edge in cycle] + [cycle[-1][1]])
            raise ValueError(f"约束图中存在环{cycle_string}")
        else:
            print("根据输入构建约束图成功.")
    
    def _forward(self):
        """前向传播，根据约束关系更新事件时间上下限
        """
        print("前向传播，根据约束关系更新事件时间上下限.")
        for node in list(nx.topological_sort(self.constraint_graph)):
            in_edges = list(self.constraint_graph.in_edges(node, data = True))
            if len(in_edges) == 0:
                # 没有入边的情况，将上界设置为下界
                self.constraint_graph.nodes[node][CEILING] = self.lower_bound
                continue
            floor: represent.CustomTime = self.constraint_graph.nodes[node][FLOOR]
            ceiling: represent.CustomTime = self.constraint_graph.nodes[node][CEILING]
            for pre_node, _, info in in_edges:
                constraint: Constraint = info[CONSTRAINT]
                curr_range = {FLOOR: floor, CEILING: ceiling}
                pre_node_range = {FLOOR: self.constraint_graph.nodes[pre_node][FLOOR], CEILING: self.constraint_graph.nodes[pre_node][CEILING]}
                new_range = constraint.forward_update(curr_range, pre_node_range)
                floor = new_range[FLOOR]
                ceiling = new_range[CEILING]
            self.constraint_graph.nodes[node][FLOOR] = floor
            self.constraint_graph.nodes[node][CEILING] = ceiling

    def _backward(self):
        """后向传播，根据约束关系随机获得事件时间值.
        """
        print("后向传播，根据约束关系随机获得事件时间值.")
        nodes = list(nx.topological_sort(self.constraint_graph))
        nodes.reverse()
        for node in nodes:
            out_edges = list(self.constraint_graph.out_edges(node, data = True))
            if len(out_edges) > 0:
                for _, next_node, info in out_edges:
                    constraint: Constraint = info[CONSTRAINT]
                    next_time = self.constraint_graph.nodes[next_node][TIME]
                    curr_range = {FLOOR: self.constraint_graph.nodes[node][FLOOR], CEILING: self.constraint_graph.nodes[node][CEILING]}
                    new_range = constraint.backward_update(next_time, curr_range)
                    self.constraint_graph.nodes[node][FLOOR] = new_range[FLOOR]
                    self.constraint_graph.nodes[node][CEILING] = new_range[CEILING]
            time_range = represent.get_time_range(self.constraint_graph.nodes[node][FLOOR], self.constraint_graph.nodes[node][CEILING])
            self.constraint_graph.nodes[node][TIME] = random.choice(time_range)

    def _get_temporal_time(self, e: event.Event) -> represent.CustomTime:
        """从约束图中，为时点事件获取时间值

        Args:
            e (event.Event): 事件

        Raises:
            ValueError: 事件不是时点事件

        Returns:
            represent.CustomTime: 事件的时间值
        """
        if e.kind == event.EventType.Temporal:
            if e.name in self.constraint_graph.nodes:
                return self.constraint_graph.nodes[e.name][TIME]
            else:
                time_range = represent.get_time_range(self.lower_bound, self.upper_bound)
                return random.choice(time_range)
        else:
            raise ValueError(f"函数_get_temporal_time()不支持的事件类型{e.kind}")
    
    def get_time_props(self, events: Sequence[event.Event]) -> list[prop.Proposition]:
        # 后向传播，随机生成时间
        self._backward()
        time_props: list[prop.Proposition] = []
        for e in events:
            if e.kind == event.EventType.Temporal:
                # 如果事件在约束图中，则添加时间约束
                e_time = self._get_temporal_time(e)
                prop_dict: dict[str, Any] = {prop.PropField.Time: e_time, prop.PropField.Event: e, prop.PropField.Kind: "temporal"}
                time_props.append(prop.Proposition(**prop_dict))
            elif e.kind == event.EventType.Durative:
                start_event: event.Event = e[event.SubEventType.StartEvent]
                end_event: event.Event = e[event.SubEventType.EndEvent]
                duration_event: event.Event = e[event.SubEventType.DurationEvent]
                start_time = self._get_temporal_time(start_event)
                start_dict = {prop.PropField.Time: start_time, prop.PropField.Event: start_event, prop.PropField.Kind: "temporal"}
                time_props.append(prop.Proposition(**start_dict))
                end_time = self._get_temporal_time(end_event)
                end_dict = {prop.PropField.Time: end_time, prop.PropField.Event: end_event, prop.PropField.Kind: "temporal"}
                time_props.append(prop.Proposition(**end_dict))
                duration_time = end_time - start_time
                duration_dict = {prop.PropField.Time: duration_time, prop.PropField.Event: duration_event, prop.PropField.Kind: "duration"}
                time_props.append(prop.Proposition(**duration_dict))
                durative_event = {prop.PropField.Event: e, prop.PropField.Kind: "durative", prop.PropField.Time: start_time, prop.PropField.EndTime: end_time, prop.PropField.Duration: duration_time}
                time_props.append(prop.Proposition(**durative_event))
            elif e.kind == event.EventType.Frequent:
                # TODO: 频率事件的处理
                pass
            else:
                raise ValueError(f"不支持的事件类型{e.kind}")
        return time_props