# encoding: utf8
# date: 2025-03-08

import element
import proposition as prop
import math
from itertools import takewhile
from typing import Optional
from enum import StrEnum

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

    def set_layer(self, curr_layer: int, curr_props: list[prop.Proposition]) -> Optional[prop.Proposition]:
        """设置节点的层级

        Args:
            curr_layer (int): 当前层级
            curr_props (list[prop.Proposition]): 当前的命题

        Returns:
            Optional[prop.Proposition]: 如果节点层数小于当前层数，返回节点的结论命题，否则返回None
        """
        conditions: list[prop.Proposition] = self[NodeField.Condition]
        for i in takewhile(lambda x: self[NodeField.ConditionLayers][x] > curr_layer, range(len(conditions))):
            if conditions[i].is_contained(curr_props):
                self[NodeField.ConditionLayers][i] = min(self[NodeField.ConditionLayers][i], curr_layer)
        self[NodeField.Layer] = max(self[NodeField.ConditionLayers])
        # 如果节点层数小于当前层数，返回结论命题，否则返回None
        return self[NodeField.Conclusion] if self[NodeField.Layer] < curr_layer else None
