# encoding: utf8
# date: 2025-03-02

"""命题推理使用的推理图
"""

import element
import config
import proposition as prop
from enum import StrEnum

class NodeField(StrEnum):
    """推理图中节点的字段
    """
    Condition = "condition" # 条件
    Conclusion = "conclusion" # 结论
    Rule = "rule" # 规则

class Node(element.Element):
    """推理图中的节点
    """
    pass