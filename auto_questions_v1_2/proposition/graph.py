# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-03

"""
创建记录推理路径的图
"""

import sys
from pathlib import Path
from functools import reduce
import random

# 将上级目录加入到sys.path中
sys.path.append(str(Path(__file__).resolve().parents[1]))

from proposition.prop import Proposition

REASON_CONJUNCTIONS = {
    "because": ["因为", "由于", "既然", "根据",],
    "another": ["另外", "再者", "此外", "而且", "并且",],
    "so": ["所以", "因此", "故", "于是", "因而",],
}

class Node:
    """节点类，表示一个推理步骤
    """
    def __init__(self, conditions: list[Proposition], conclusion: Proposition, layer: int):
        """初始化一个节点，这个节点表示一个推理步骤

        Args:
            conditions (list[Proposition]): 推理的前提条件，每个元素是一个命题
            conclusion (Proposition): 推理的结论，是一个命题
        """
        self.conditions = conditions
        self.conclusion = conclusion
        self.layer = layer

    def state(self, temps: dict[str, list[str]]) -> str:
        """返回节点的陈述

        Args:
            temps (dict[str, list[str]]): 模板字典

        Returns:
            str: 节点的陈述
        """
        global REASON_CONJUNCTIONS
        sentences = ""
        for i, p in enumerate(self.conditions):
            sentences += random.choice(REASON_CONJUNCTIONS["because"]) + p.state(temps) + "，"
            if i < len(self.conditions) - 1:
                sentences += random.choice(REASON_CONJUNCTIONS["another"])
        sentences += random.choice(REASON_CONJUNCTIONS["so"]) + self.conclusion.state(temps)
        return sentences
    
    def __eq__(self, other) -> bool:
        """判断两个节点是否相等
        
        Args:
            other (Node): 另一个节点
            
        Returns:
            bool: 如果两个节点相等，返回True，否则返回False"""
        if not isinstance(other, Node):
            return False
        if len(self.conditions) != len(other.conditions):
            return False
        for i in range(len(self.conditions)):
            if self.conditions[i] != other.conditions[i]:
                return False
        return self.conclusion == other.conclusion

class Graph:
    """图类，表示一个推理图
    """
    def __init__(self, init_props: list[Proposition] = [], knowledge_props: list[Proposition] = []):
        """初始化一个图

        Args:
            init_props (list[Proposition], optional): 初始的命题. Defaults to [].
            knowledge_props (list[Proposition], optional): 知识库中的命题. Defaults to [].
        """
        self.nodes: list[Node] = []
        # 11-07更新：将知识添加到查找过的结论命题和路径当中
        self.conclusion_props: list[Proposition] = init_props + knowledge_props # 已经查找过的结论命题
        self.paths: list[list[Node]] = [[]] * len(self.conclusion_props) # 结论命题的路径
        # 11-24更新：记录图的层级数
        self.layers: int = 0 # 图的层级数，初始化为0

    def add_node(self, node: Node) -> bool:
        """添加一个节点到图中

        Args:
            node (Node): 要添加的节点

        Returns:
            bool: 如果添加成功，返回True，否则返回False
        """
        assert isinstance(node, Node), "node must be an instance of Node"
        # 检查已有节点是否有相同的节点
        for n in self.nodes:
            if n == node: # 如果有相同的节点，直接返回，不添加
                return False
        self.nodes.append(node)
        # 更新图的层级数
        if node.layer > self.layers:
            self.layers = node.layer
        return True

    # 返回一种比较短的推理路径
    # TODO: 优化算法，减少重复计算
    def backtrace(self, conclusion: Proposition) -> list[Node]:
        """回溯推理路径上的节点，返回一种比较短的推理路径。\n
        目前在每次检索时采用局部最优的算法，因此无法证明这是最短的推理路径

        Args:
            conclusion (Proposition): 推理路径的终点(结论)

        Returns:
            list[Node]: 推理路径
        """
        # 检查是否已经查找过这个结论命题，如果查找过，直接返回路径
        for i, p in enumerate(self.conclusion_props):
            if p == conclusion:
                return self.paths[i]
        
        # 如果没有查找过这个结论命题，查找并返回路径
        trace_nodes: list[Node] = [] # 获取结论属性为结论命题的节点
        for node in self.nodes:
            if node.conclusion == conclusion:
                trace_nodes.append(node)
        if len(trace_nodes) == 0:
            self.conclusion_props.append(conclusion)
            self.paths.append([])
            return []
        # 对trace_nodes进行排序
        # 需要选出层数最浅的节点，如果层数相同则要求前件最少
        trace_nodes.sort(key=lambda x: (x.layer, len(x.conditions)))
        conclusion_paths = [self.backtrace(p) for p in trace_nodes[0].conditions]
        front_path: list[Node] = reduce(lambda x, y: x + y, conclusion_paths, [])
        curr_path = [i for i in front_path] + [trace_nodes[0]]
        return curr_path

    def certain_layer_props(self, layer: int) -> list[Proposition]:
        """返回某一层的全部命题集合

        Args:
            layer (int): 层级

        Returns:
            list[Proposition]: 层级为layer的命题
        """
        # 检索所有位于该层的节点的结论命题
        conclusions =  [node.conclusion for node in self.nodes if node.layer == layer]
        # 判断结论命题的最浅层次是否为本层
        return [c for c in conclusions if self.layer_query(c) == layer]

    @property
    def deepest_layer_props(self) -> list[Proposition]:
        """返回最深层的全部命题集合

        Returns:
            list[Proposition]: 最深层的全部命题集合
        """
        # 从最深层开始查找，找到第一个非空的层级
        for layer in range(self.layers, 0, -1):
            if len(prop_list := self.certain_layer_props(layer)) > 0:
                return prop_list # 返回最深层的全部命题集合
        return []

    def layer_query(self, prop: Proposition) -> int:
        """查询某个命题所在的最小层级，如果没有找到，返回-1

        Args:
            prop (Proposition): 要查询的命题

        Returns:
            int: 命题所在的层级，如果没有找到，返回-1
        """
        layer: int = self.layers + 1 # 初始化为一个不可能的层级
        # 遍历所有节点，找到结论命题为prop的节点，取最小的层级
        for node in self.nodes:
            if node.conclusion == prop:
                layer = min(layer, node.layer)
        if layer == self.layers + 1:
            return -1
        return layer