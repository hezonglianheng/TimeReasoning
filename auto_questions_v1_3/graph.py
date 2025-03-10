# encoding: utf8
# date: 2025-03-02

"""命题推理使用的推理图
"""

import config
import proposition as prop
import mynode
import rule
from tqdm import tqdm
import math
from collections.abc import Sequence
from typing import Optional
from itertools import takewhile
from pathlib import Path

class ReasoningGraph:
    """推理图，内含全面的推理结果，是程序的核心组件之一\n
    reason()方法执行一次推理\n
    set_node_layers()方法设置节点的层级(执行二次推理)\n
    """

    def __init__(self, init_props: Sequence[prop.Proposition], rules: Sequence[rule.Rule], knowledge_props: Optional[Sequence[prop.Proposition]] = None):
        """初始化推理图

        Args:
            init_props (Sequence[prop.Proposition]): 推理图中的初始命题
            rules (Sequence[rule.Rule]): 推理图中可用的推理规则
            knowledge_props (Optional[Sequence[prop.Proposition]], optional): 知识命题. 默认为None.
        """
        self.init_props: list[prop.Proposition] = list(init_props) # 推理图中的初始命题
        self.reasoning_rules: list[rule.Rule] = list(rules) # 推理图中可用的推理规则
        self.knowledge_props: list[prop.Proposition] = list(knowledge_props) if knowledge_props is not None else []
        self.nodes: list[mynode.Node] = [] # 推理图中的节点
        self.deepest_layer: int = -1 # 推理图中最深的层级

    def add_nodes(self, nodes: Sequence[mynode.Node]):
        """添加节点

        Args:
            nodes (Sequence[mynode.Node]): 节点序列
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
        conclusions: list[prop.Proposition] = []
        for node in self.nodes:
            node_conclusion: prop.Proposition = node[mynode.CONCLUSION]
            if not node_conclusion.is_contained(conclusions):
                conclusions.append(node_conclusion)
        return conclusions

    def get_all_props(self) -> list[prop.Proposition]:
        """获取推理图中的所有命题

        Returns:
            list[prop.Proposition]: 命题列表
        """
        all_props: list[prop.Proposition] = []
        for node in tqdm(self.nodes, desc="获取所有命题"):
            condition: list[prop.Proposition] = node[mynode.CONDITION]
            conclusion: prop.Proposition = node[mynode.CONCLUSION]
            for p in condition:
                if not p.is_contained(all_props):
                    all_props.append(p)
            if not conclusion.is_contained(all_props):
                all_props.append(conclusion)
        return all_props

    def reason(self, new_props: Optional[list[prop.Proposition]] = None):
        """执行推理，得到完整的推理图

        Args:
            new_props (Optional[list[prop.Proposition]], optional): 新的命题. 用于增量式推理. 默认为None.
        """
        # 删除graph.txt文件
        if Path(config.CURR_SETTING_DIR).exists():
            graph_file_path = Path(config.CURR_SETTING_DIR) / config.GRAPH_FILE
            if graph_file_path.exists():
                graph_file_path.unlink()
        reason_count: int = 0
        if new_props is None:
            old_prop_list: list[prop.Proposition] = []
            curr_prop_list: list[prop.Proposition] = self.init_props + self.knowledge_props
        else:
            assert len(self.nodes) > 0, "没有节点，不适用增量推理"
            old_prop_list: list[prop.Proposition] = self.get_all_props()
            curr_prop_list: list[prop.Proposition] = new_props
        assert len(curr_prop_list) > 0, "没有命题可以推理"
        assert len(self.reasoning_rules) > 0, "没有推理规则"
        while True:
            reason_count += 1
            curr_nodes: list[mynode.Node] = []
            for rule in self.reasoning_rules:
                rule_result = rule.reason(old_prop_list, curr_prop_list, reason_count)
                curr_nodes.extend(rule_result)
            curr_conclusions: list[prop.Proposition] = [i[mynode.CONCLUSION] for i in curr_nodes]
            new_prop_list: list[prop.Proposition] = []
            for p in tqdm(curr_conclusions, desc="检查新结论命题是否已存在"):
                if not p.is_contained(old_prop_list) and not p.is_contained(curr_prop_list) and not p.is_contained(new_prop_list):
                    new_prop_list.append(p)
            with open(Path(config.CURR_SETTING_DIR) / config.GRAPH_FILE, "a", encoding="utf8") as f:
                for node in curr_nodes:
                    conditions: str = " && ".join([p.translate(config.CHINESE) for p in node[mynode.CONDITION]])
                    conclusion: str = node[mynode.CONCLUSION].translate(config.CHINESE)
                    f.write(f"{conditions} => {conclusion}\n")
            if len(new_prop_list) == 0:
                self.add_nodes(curr_nodes)
                print("所有新结论命题都已存在，推理结束")
                break
            self.add_nodes(curr_nodes)
            old_prop_list.extend(curr_prop_list)
            curr_prop_list = new_prop_list
        print(f"推理结束，共执行{reason_count}次推理，得到{len(self.nodes)}个节点")

    def set_node_layers(self, chosen_props: list[prop.Proposition]):
        """设置节点的层级，本质上是第二轮推理

        Args:
            chosen_props (list[prop.Proposition]): 选择的命题
        """
        # 重置节点的层级
        for node in self.nodes:
            node[mynode.LAYER] = math.inf
            node[mynode.CONDITION_LAYERS] = [math.inf] * len(node[mynode.NodeField.Condition])
        curr_layer_props: list[prop.Proposition] = chosen_props + self.knowledge_props
        next_layer_props: list[prop.Proposition] = []
        layer: int = 0
        while any([i[mynode.LAYER] > layer for i in self.nodes]):
            layer += 1
            print(f"设置第{layer}层节点")
            for node in takewhile(lambda x: x[mynode.LAYER] > layer, self.nodes):
                conclusion = node.set_layer(layer, curr_layer_props)
                if conclusion and conclusion.is_contained(next_layer_props):
                    next_layer_props.append(conclusion)
            print(f"第{layer}层节点设置完毕，已经设置{len(next_layer_props)}个结论命题")
            curr_layer_props = next_layer_props + self.knowledge_props
            next_layer_props = []
        else:
            self.deepest_layer = layer
            print(f"设置层级结束，共设置{layer}层")

    def get_deepest_conclusions(self) -> list[prop.Proposition]:
        """获取最深层次推理图节点的结论命题

        Returns:
            list[prop.Proposition]: 最深层次推理图节点的结论命题
        """
        assert self.deepest_layer >= 0, "尚未进行二次推理"
        conclusion_list: list[prop.Proposition] = []
        for node in takewhile(lambda x: x[mynode.LAYER] == self.deepest_layer, self.nodes):
            node_conclusion: prop.Proposition = node[mynode.CONCLUSION]
            if not node_conclusion.is_contained(conclusion_list):
                conclusion_list.append(node_conclusion)
        return conclusion_list