# encoding: utf8
# date: 2025-03-02

"""命题推理使用的推理图
"""

import element
import config
import proposition as prop
import rule
from enum import StrEnum
import math
from collections.abc import Sequence
from typing import Optional
from itertools import takewhile

class NodeField(StrEnum):
    """推理图中节点的字段
    """
    Condition = "condition" # 条件
    Conclusion = "conclusion" # 结论
    Rule = "rule" # 规则
    Layer = "layer" # 层级
    ConditionLayers = "condition_layers" # 条件的层级

class Node(element.Element):
    """推理图中的节点
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self[NodeField.ConditionLayers] = [math.inf] * len(self[NodeField.Condition]) # 条件的层级
        self[NodeField.Layer] = math.inf # 默认层级为无穷大

    def translate(self, lang, require = None, **kwargs):
        # TODO: 推理图上节点的翻译方法，用于生成CoT
        pass

    def set_layer(self, curr_layer: int, curr_props: list[prop.Proposition]):
        """设置节点的层级

        Args:
            curr_layer (int): 当前层级
            curr_props (list[prop.Proposition]): 当前的命题
        """
        conditions: list[prop.Proposition] = self[NodeField.Condition]
        for i in takewhile(lambda x: self[NodeField.ConditionLayers][x] > curr_layer, range(len(conditions))):
            if conditions[i].is_contained(curr_props):
                self[NodeField.ConditionLayers][i] = min(self[NodeField.ConditionLayers][i], curr_layer)
        self[NodeField.Layer] = max(self[NodeField.ConditionLayers])

class ReasoningGraph:
    """推理图，内含全面的推理结果，是程序的核心组件之一\n
    reason()方法执行一次推理\n
    set_node_layers()方法设置节点的层级(执行二次推理)\n
    """

    def __init__(self, init_props: Sequence[prop.Proposition], rules: Sequence[rule.Rule]):
        """初始化推理图

        Args:
            init_props (Sequence[prop.Proposition]): 推理图中的初始命题
            rules (Sequence[rule.Rule]): 推理图中可用的推理规则
        """
        self.init_props: list[prop.Proposition] = list(init_props) # 推理图中的初始命题
        self.reasoning_rules: list[rule.Rule] = list(rules) # 推理图中可用的推理规则
        self.nodes: list[Node] = [] # 推理图中的节点
        self.deepest_layer: int = -1 # 推理图中最深的层级

    def add_nodes(self, nodes: Sequence[Node]):
        """添加节点

        Args:
            nodes (Sequence[Node]): 节点序列
        """
        self.nodes.extend(nodes)

    def add_rules(self, rules: Sequence[rule.Rule]):
        """添加推理规则

        Args:
            rules (Sequence[rule.Rule]): 推理规则序列
        """
        name_set: set[str] = [i.name for i in self.reasoning_rules]
        for r in rules:
            if r.name not in name_set:
                self.reasoning_rules.append(r)
                name_set.add(r.name)
            else:
                print(f"增加规则时，发现规则{r.name}已存在")

    def get_conclusions(self) -> list[prop.Proposition]:
        """获取推理图中的所有结论命题

        Returns:
            list[prop.Proposition]: 结论命题列表
        """
        return [i[NodeField.Conclusion] for i in self.nodes]

    def reason(self, new_props: Optional[list[prop.Proposition]] = None):
        """执行推理，得到完整的推理图

        Args:
            new_props (Optional[list[prop.Proposition]], optional): 新的命题. 用于增量式推理. 默认为None.
        """
        reason_count: int = 0
        if new_props is None:
            curr_prop_list: list[prop.Proposition] = self.init_props
        else:
            assert len(self.nodes) > 0, "没有节点，不适用增量推理"
            curr_prop_list: list[prop.Proposition] = new_props + self.get_conclusions()
        assert len(curr_prop_list) > 0, "没有命题可以推理"
        assert len(self.reasoning_rules) > 0, "没有推理规则"
        curr_nodes: list[Node] = []
        while True:
            reason_count += 1
            print(f"执行第{reason_count}次推理")
            for rule in self.reasoning_rules:
                print(f"开始执行规则{rule.name}")
                rule_result = rule.reason(curr_prop_list)
                print(f"执行规则{rule.name}成功")
                curr_nodes.extend(rule_result)
            if len(curr_nodes) == 0:
                break
            self.add_nodes(curr_nodes)
            curr_prop_list = self.get_conclusions()

    def set_node_layers(self, chosen_props: list[prop.Proposition]):
        """设置节点的层级，本质上是第二轮推理

        Args:
            chosen_props (list[prop.Proposition]): 选择的命题
        """
        # 重置节点的层级
        for node in self.nodes:
            node[NodeField.Layer] = math.inf
            node[NodeField.ConditionLayers] = [math.inf] * len(node[NodeField.Condition])
        curr_layer_props: list[prop.Proposition] = chosen_props
        layer: int = 0
        while any([i[NodeField.Layer] > layer for i in self.nodes]):
            layer += 1
            print(f"设置第{layer}层节点")
            for node in takewhile(lambda x: x[NodeField.Layer] > layer, self.nodes):
                node.set_layer(layer, curr_layer_props)
        else:
            self.deepest_layer = layer
            print(f"设置层级结束，共设置{layer}层")

    def get_deepest_conclusions(self) -> list[prop.Proposition]:
        """获取最深层次推理图节点的结论命题

        Returns:
            list[prop.Proposition]: 最深层次推理图节点的结论命题
        """
        assert self.deepest_layer >= 0, "尚未进行二次推理"
        return [i[NodeField.Conclusion] for i in self.nodes if i[NodeField.Layer] == self.deepest_layer]