# encoding: utf8
# date: 2025-03-08

import element
import proposition as prop
import config
import math
from typing import Optional
import random
from warnings import warn

# constants.
CONDITION = "condition"
CONCLUSION = "conclusion"
RULE = "rule"
LAYER = "layer"
CONDITION_LAYERS = "condition_layers"
# 12-19新增：记录从初始命题推至该节点所使用的推理链步数信息
CHAIN_LENGTH = "chain_length"
"""记录从初始命题推至该节点所使用的推理链步数信息"""
LAST_NODES = "last_nodes"
"""记录推至该节点所使用的之前一层的节点信息"""

class Node(element.Element):
    """推理图中的节点
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self[CONDITION_LAYERS] = [math.inf] * len(self[CONDITION]) # 条件的层级
        self[LAYER] = math.inf # 默认层级为无穷大
        self[LAST_NODES] = [None] * len(self[CONDITION]) # 12-19新增：记录推至该节点所使用的之前一层的节点信息
        self[CHAIN_LENGTH] = 1 # 12-19新增：记录从初始命题推至该节点所使用的推理链步数信息

    def translate(self, lang: str, require = None, **kwargs) -> str:
        """翻译节点为特定语言的字符串表示，表示当前节点的推理过程

        Args:
            lang (str): 语言代码，例如 "en" 或 "cn"
            require (str, optional): 翻译需求，默认为 None
            **kwargs: 其他可选参数

        Returns:
            str: 节点的推理过程的字符串表示
        """
        cot_str = ""
        conditions: list[prop.Proposition] = self[CONDITION]
        conclusion: prop.Proposition = self[CONCLUSION]
        for i in range(len(conditions)):
            if i == 0:
                curr_str = random.choice(config.LANG_CONFIG[lang]["because"]) + config.SEPARATE[lang] + conditions[i].translate(lang)
            else:
                curr_str = random.choice(config.LANG_CONFIG[lang]["and"]) + config.SEPARATE[lang] + random.choice(config.LANG_CONFIG[lang]["because"]) + config.SEPARATE[lang] + conditions[i].translate(lang)
            cot_str += curr_str + config.LANG_CONFIG[lang]["comma"] + config.SEPARATE[lang]
        cot_str += random.choice(config.LANG_CONFIG[lang]["so"]) + config.SEPARATE[lang] + conclusion.translate(lang) + config.LANG_CONFIG[lang]["full_stop"]
        return cot_str

    # 12-19新增：增加重置节点的函数
    def reset(self) -> None:
        """重置节点的层级信息，包括条件层级、节点层级、上一层节点信息和推理链长度
        """
        self[CONDITION_LAYERS] = [math.inf] * len(self[CONDITION])
        self[LAYER] = math.inf
        self[LAST_NODES] = [None] * len(self[CONDITION])
        self[CHAIN_LENGTH] = 1

    # 08-25修改：函数不再提供返回
    # def set_layer(self, curr_layer: int, curr_props: list[prop.Proposition]) -> Optional[prop.Proposition]:
    def set_layer(self, curr_layer: int, curr_props: list[prop.Proposition]) -> None:
        """设置节点的层级

        Args:
            curr_layer (int): 当前层级
            curr_props (list[prop.Proposition]): 当前的命题
        """
        warn("set_layer方法已废弃，请使用set_node_info方法代替", DeprecationWarning)
        conditions: list[prop.Proposition] = self[CONDITION]
        for i, p in enumerate(conditions):
            if p.is_contained(curr_props):
                self[CONDITION_LAYERS][i] = min(self[CONDITION_LAYERS][i], curr_layer)
        self[LAYER] = max(self[CONDITION_LAYERS])
        # 函数不再提供返回
        # 如果节点层数小于当前层数，返回结论命题，否则返回None
        # return self[CONCLUSION] if self[LAYER] <= curr_layer else None

    # 12-19新增：增加设置节点信息的函数
    def set_node_info(self, curr_layer: int, curr_props: list[prop.Proposition], last_nodes: list[Optional['Node']]) -> None:
        """设置节点的层级、涉及到的上一个节点和推理链长度等信息

        Args:
            curr_layer (int): 当前层级
            curr_props (list[prop.Proposition]): 当前的命题
            last_nodes (list[Optional['Node']]): 推至该节点所使用的之前一层的节点信息
        """
        conditions: list[prop.Proposition] = self[CONDITION]
        for i, p in enumerate(conditions):
            for cp, cn in zip(curr_props, last_nodes):
                if p == cp:
                    self[CONDITION_LAYERS][i] = min(self[CONDITION_LAYERS][i], curr_layer)
                    self[LAST_NODES][i] = cn
                    if cn is not None:
                        self[CHAIN_LENGTH] += cn[CHAIN_LENGTH]
                    break
        self[LAYER] = max(self[CONDITION_LAYERS])

    # 12-19新增：增加获取节点信息的函数
    def get_precede_nodes(self) -> list['Node']:
        """获得推出本节点涉及的所有节点的信息
        """
        before_nodes: list['Node'] = []
        last_nodes: list['Node'] = [i for i in self[LAST_NODES] if i is not None]
        for ln in last_nodes:
            before_nodes.extend(ln.get_precede_nodes())
        return before_nodes + last_nodes