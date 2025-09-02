# encoding: utf8
# date: 2025-02-23

"""根据输入文件中的约束关系，为事件获得满足约束的时间值
"""

import config
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
CONSTRAINT = "constraint"
TIME = "time"
# 约束中的字段
MAIN_EVENT = "main_event"
STD_EVENT = "std_event"
CONSTRAINT_TYPE = "constraint_type"
FLOOR = "floor"
CEILING = "ceiling"
# 约束类型
BEFORE = "before"
AFTER = "after"
SIMULTANEOUS = "simultaneous"

class Constraint(element.Element):
    """约束类
    """
    def __init__(self, name = "", kind = "", **kwargs):
        # 05-03修订：增加对std_event和main_event的记录
        constraint_dict = {STD_EVENT: kwargs[STD_EVENT], MAIN_EVENT: kwargs[MAIN_EVENT]}
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

    def translate(self, lang, require = None, **kwargs):
        return super().translate(lang, require, **kwargs)
    
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
        main_floor = main_times[FLOOR]
        main_ceiling = main_times[CEILING]
        if self.kind == BEFORE:
            if self.has_attr(FLOOR):
                std_ceiling: represent.CustomTime = std_ceiling - self[FLOOR]
                main_ceiling = min(main_ceiling, std_ceiling)
            if self.has_attr(CEILING):
                std_floor: represent.CustomTime = std_floor - self[CEILING]
                main_floor = max(main_floor, std_floor)
        elif self.kind == AFTER:
            if self.has_attr(FLOOR):
                std_floor: represent.CustomTime = std_floor + self[FLOOR]
                main_floor = max(main_floor, std_floor)
            if self.has_attr(CEILING):
                std_ceiling: represent.CustomTime = std_ceiling + self[CEILING]
                main_ceiling = min(main_ceiling, std_ceiling)
        elif self.kind == SIMULTANEOUS:
            main_floor = max(std_floor, main_floor)
            main_ceiling = min(std_ceiling, main_ceiling)
        return {FLOOR: main_floor, CEILING: main_ceiling}

    def backward_update(self, main_times: dict[str, represent.CustomTime], std_times: dict[str, represent.CustomTime]) -> dict[str, represent.CustomTime]:
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
                new_floor: represent.CustomTime = main_times[FLOOR] + self[FLOOR]
                std_floor = max(std_floor, new_floor)
            if self.has_attr(CEILING):
                new_ceiling: represent.CustomTime = main_times[CEILING] + self[CEILING]
                std_ceiling = min(std_ceiling, new_ceiling)
        elif self.kind == AFTER:
            if self.has_attr(CEILING):
                new_floor: represent.CustomTime = main_times[FLOOR] - self[CEILING]
                std_floor = max(std_floor, new_floor)
            if self.has_attr(FLOOR):
                new_ceiling: represent.CustomTime = main_times[CEILING] - self[FLOOR]
                std_ceiling = min(std_ceiling, new_ceiling)
        elif self.kind == SIMULTANEOUS:
            # assert std_floor <= main_times <= std_ceiling, f"约束中参考事件{self[STD_EVENT]}时间范围({std_floor}-{std_ceiling})不包含主要事件{self[MAIN_EVENT]}时间{main_times}"
            # 直接利用参考时间修改主要事件时间范围
            std_floor = max(std_floor, main_times[FLOOR])
            std_ceiling = min(std_ceiling, main_times[CEILING])
        else:
            raise ValueError(f"不支持的约束类型{self.kind}")
        assert std_floor <= std_ceiling, f"时间范围不合法: {std_floor} - {std_ceiling}"
        return {FLOOR: std_floor, CEILING: std_ceiling}

class ConstraintMachine:
    def __init__(self, event_names: Sequence[str], constraint_rules: Sequence[dict], upper_bound: represent.CustomTime, lower_bound: represent.CustomTime, distribution_mode: str = "random"):
        """
        初始化约束机

        Args:
            event_names (Sequence[str]): 事件名称列表
            constraint_rules (Sequence[dict]): 约束规则列表
            upper_bound (represent.CustomTime): 上界时间
            lower_bound (represent.CustomTime): 下界时间
            distribution_mode (str): 事件时间分配方式，默认为"random". 目前可用的策略有：
                - random: 为每个事件随机选择时间
                - individual: 每个事件选择的时间互不相同
        """
        self.event_names = event_names
        self.constraint_rules = constraint_rules
        assert upper_bound > lower_bound, "约束机类中上界应大于下界"
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.constraint_graph = nx.DiGraph()
        # 03-11新增：增加对于事件顺序的记录
        self.event_order: list[tuple[represent.CustomTime, event.Event]] = []
        # 09-02新增：增加对于事件时间分配方式的记录
        self.distribution_mode = distribution_mode
        """事件时间的分配方式"""
        self.had_chosen_time: list[represent.CustomTime] = []
        """记录已经被选择过的时间"""
        self._construct()
        # 05-04移除：不在初始化时进行前向传播，而是每次求取事件的时间时再进行
        # self._forward()

    def _construct(self):
        """根据输入构造约束图
        """
        # 设置约束图中的节点
        for name in self.event_names:
            self.constraint_graph.add_node(name, **{FLOOR: self.lower_bound, CEILING: self.upper_bound})
        # 设置约束图中的边
        for rule in self.constraint_rules:
            constraint = Constraint(**rule)
            self.constraint_graph.add_edge(rule[STD_EVENT], rule[MAIN_EVENT], **{CONSTRAINT: constraint})
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
            """
            if len(in_edges) == 0:
                # 没有入边的情况考虑出边的数量
                out_edges = list(self.constraint_graph.out_edges(node, data = True))
                # 没有出边的情况，时间范围为全局范围
                if len(out_edges) == 0:
                    self.constraint_graph.nodes[node][FLOOR] = self.lower_bound
                    self.constraint_graph.nodes[node][CEILING] = self.upper_bound
                    continue
                # 有出边的情况，将下界设为上界
                self.constraint_graph.nodes[node][CEILING] = self.lower_bound
                continue
            """
            floor: represent.CustomTime = self.constraint_graph.nodes[node][FLOOR]
            ceiling: represent.CustomTime = self.constraint_graph.nodes[node][CEILING]
            for pre_node, _, info in in_edges:
                constraint: Constraint = info[CONSTRAINT]
                curr_range = {FLOOR: floor, CEILING: ceiling}
                pre_node_range = {FLOOR: self.constraint_graph.nodes[pre_node][FLOOR], CEILING: self.constraint_graph.nodes[pre_node][CEILING]}
                new_range = constraint.forward_update(curr_range, pre_node_range)
                floor = new_range[FLOOR]
                ceiling = new_range[CEILING]
            assert floor < ceiling or floor == ceiling, f"事件{node}的时间范围不合法: {floor} - {ceiling}"
            self.constraint_graph.nodes[node][FLOOR] = floor
            self.constraint_graph.nodes[node][CEILING] = ceiling
        
        for node in self.constraint_graph.nodes:
            print(f"事件{node}的时间范围: {self.constraint_graph.nodes[node][FLOOR]} - {self.constraint_graph.nodes[node][CEILING]}")
            # assert floor <= ceiling, f"事件{node}的时间范围不合法: {floor} - {ceiling}"

    def _backward(self):
        """后向传播，根据约束关系更新事件时间上下限
        """
        print("后向传播，根据约束关系更新事件时间上下限.")
        nodes = list(nx.topological_sort(self.constraint_graph))
        nodes.reverse()
        for node in nodes:
            floor: represent.CustomTime = self.constraint_graph.nodes[node][FLOOR]
            ceiling: represent.CustomTime = self.constraint_graph.nodes[node][CEILING]
            out_edges = list(self.constraint_graph.out_edges(node, data = True))
            if len(out_edges) > 0:
                for _, next_node, info in out_edges:
                    constraint: Constraint = info[CONSTRAINT]
                    # next_time = self.constraint_graph.nodes[next_node][TIME]
                    next_node_range = {FLOOR: self.constraint_graph.nodes[next_node][FLOOR], CEILING: self.constraint_graph.nodes[next_node][CEILING]}
                    curr_range = {FLOOR: floor, CEILING: ceiling}
                    new_range = constraint.backward_update(next_node_range, curr_range)
                    floor = new_range[FLOOR]
                    ceiling = new_range[CEILING]
            self.constraint_graph.nodes[node][FLOOR] = floor
            self.constraint_graph.nodes[node][CEILING] = ceiling
            """
            time_range = represent.get_time_range(self.constraint_graph.nodes[node][FLOOR], self.constraint_graph.nodes[node][CEILING])
            chosen_time = random.choice(time_range)
            self.constraint_graph.nodes[node][TIME] = chosen_time
            print(f"事件{node}的时间值设置为: {chosen_time}")
            """

    def _set_time(self):
        nodes = list(nx.topological_sort(self.constraint_graph))
        for node in nodes:
            in_edges = list(self.constraint_graph.in_edges(node, data = True))
            for pre_node, _, info in in_edges:
                constraint: Constraint = info[CONSTRAINT]
                curr_range = {FLOOR: self.constraint_graph.nodes[node][FLOOR], CEILING: self.constraint_graph.nodes[node][CEILING]}
                pre_node_range = {FLOOR: self.constraint_graph.nodes[pre_node][FLOOR], CEILING: self.constraint_graph.nodes[pre_node][CEILING]}
                new_range = constraint.forward_update(curr_range, pre_node_range)
                self.constraint_graph.nodes[node][FLOOR] = new_range[FLOOR]
                self.constraint_graph.nodes[node][CEILING] = new_range[CEILING]
            # 随机得到一个时间值
            time_range = represent.get_time_range(self.constraint_graph.nodes[node][FLOOR], self.constraint_graph.nodes[node][CEILING])
            # 09-02修改：根据不同的时间分配方式执行不同的策略
            if self.distribution_mode == "random":
                chosen_time = random.choice(time_range)
            elif self.distribution_mode == "individual":
                candidate_times = [i for i in time_range if not i.is_contained(self.had_chosen_time)]
                assert len(candidate_times) > 0, f"事件范围内的每个时间点都被耗尽，事件{node}没有可用的时间"
                chosen_time = random.choice(candidate_times)
                self.had_chosen_time.append(chosen_time)
            # 将时间值、上下限都设置为chosen_time
            self.constraint_graph.nodes[node][TIME] = chosen_time
            self.constraint_graph.nodes[node][FLOOR] = chosen_time
            self.constraint_graph.nodes[node][CEILING] = chosen_time
            print(f"事件{node}的时间值设置为: {chosen_time}")

    def _get_temporal_time(self, e: event.Event) -> represent.CustomTime:
        """从约束图中，为时点事件获取时间值

        Args:
            e (event.Event): 事件

        Raises:
            ValueError: 事件不是时点事件

        Returns:
            represent.CustomTime: 事件的时间值
        """
        if e.kind == event.TEMPORAL:
            if e.name in self.constraint_graph.nodes:
                return self.constraint_graph.nodes[e.name][TIME]
            else:
                time_range = represent.get_time_range(self.lower_bound, self.upper_bound)
                return random.choice(time_range)
        else:
            raise ValueError(f"函数_get_temporal_time()不支持的事件类型{e.kind}")
    
    def get_time_props(self, events: Sequence[event.Event]) -> list[prop.Proposition]:
        """根据事件生成时间命题

        Args:
            events (Sequence[event.Event]): 事件列表

        Raises:
            ValueError: 事件类型不合法

        Returns:
            list[prop.Proposition]: 时间命题列表
        """
        self._forward()
        # 后向传播，随机生成时间
        self._backward()
        # 获得时间值
        self._set_time()
        # 03-11新增：清空event_order
        self.event_order.clear()
        time_props: list[prop.Proposition] = []
        for e in events:
            if e.kind == event.TEMPORAL:
                # 如果事件在约束图中，则添加时间约束
                e_time = self._get_temporal_time(e)
                prop_dict: dict[str, Any] = {prop.TIME: e_time, prop.EVENT: e, prop.KIND: "temporal"}
                time_props.append(prop.Proposition(**prop_dict))
                # 03-11新增：将事件添加到event_order中
                self.event_order.append((e_time, e))
            elif e.kind == event.DURATIVE:
                start_event: event.Event = e[event.START_EVENT]
                end_event: event.Event = e[event.END_EVENT]
                duration_event: event.Event = e[event.DURATION_EVENT]
                start_time = self._get_temporal_time(start_event)
                start_dict = {prop.TIME: start_time, prop.EVENT: start_event, prop.KIND: "temporal"}
                time_props.append(prop.Proposition(**start_dict))
                end_time = self._get_temporal_time(end_event)
                end_dict = {prop.TIME: end_time, prop.EVENT: end_event, prop.KIND: "temporal"}
                time_props.append(prop.Proposition(**end_dict))
                duration_time = end_time - start_time
                duration_dict = {prop.TIME: duration_time, prop.EVENT: duration_event, prop.KIND: "duration"}
                time_props.append(prop.Proposition(**duration_dict))
                durative_event = {prop.EVENT: e, prop.KIND: "durative", prop.TIME: start_time, prop.END_TIME: end_time, prop.DURATION: duration_time}
                time_props.append(prop.Proposition(**durative_event))
                # 03-11新增：将事件添加到event_order中
                self.event_order.append((start_time, e))
            elif e.kind == event.FREQUENT:
                # TODO: 频率事件的处理
                pass
            else:
                raise ValueError(f"不支持的事件类型{e.kind}")
        # 03-11新增：对event_order进行排序
        self.event_order.sort(key = lambda x: x[0])
        return time_props