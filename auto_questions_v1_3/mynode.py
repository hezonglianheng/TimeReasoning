# encoding: utf8
# date: 2025-03-08

import element
import proposition as prop
import math
from typing import Optional

# constants.
CONDITION = "condition"
CONCLUSION = "conclusion"
RULE = "rule"
LAYER = "layer"
CONDITION_LAYERS = "condition_layers"

class Node(element.Element):
    """推理图中的节点
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self[CONDITION_LAYERS] = [math.inf] * len(self[CONDITION]) # 条件的层级
        self[LAYER] = math.inf # 默认层级为无穷大

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
        conditions: list[prop.Proposition] = self[CONDITION]
        for i, p in enumerate(conditions):
            if p.is_contained(curr_props):
                self[CONDITION_LAYERS][i] = min(self[CONDITION_LAYERS][i], curr_layer)
        self[LAYER] = max(self[CONDITION_LAYERS])
        # 如果节点层数小于当前层数，返回结论命题，否则返回None
        return self[CONCLUSION] if self[LAYER] <= curr_layer else None
