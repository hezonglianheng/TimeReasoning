# encoding: utf8
# date: 2025-02-23

"""根据输入文件中的约束关系，为事件获得满足约束的时间值
"""

import config
import element
import represent
import proposition
import networkx as nx
from collections.abc import Sequence
from typing import Optional
import random

# constants.
MAIN_EVENT = "main_event"
STD_EVENT = "std_event"
CONSTRAINT_TYPE = "constraint_type"
FLOOR = "floor"
CEILING = "ceiling"
CONSTRAINT = "constraint"
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
        pass

class ConstraintMachine:
    def __init__(self, event_names: Sequence[str], constraint_rules: Sequence[dict], upper_bound: represent.CustomTime, lower_bound: represent.CustomTime):
        self.event_names = event_names
        self.constraint_rules = constraint_rules
        assert upper_bound > lower_bound, "约束机类中上界应大于下界"
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.constraint_graph = nx.DiGraph()
        self._construct()

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
        print("后向传播，根据约束关系获得事件时间值.")