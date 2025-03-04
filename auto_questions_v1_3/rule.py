# encoding: utf8
# date: 2025-03-02

"""命题推理使用的推理规则
"""

import element
import config
import proposition as prop
import graph
import json5
from tqdm import tqdm
from itertools import permutations
from enum import StrEnum
from collections.abc import Sequence
import math

class RuleType(StrEnum):
    """命题推理规则类型
    """
    Rule = "rule" # 推理规则
    Relation = "relation" # 命题间关系

class RuleField(StrEnum):
    """命题推理规则的字段
    """
    Condition = "condition" # 条件
    Conclusion = "conclusion" # 结论
    Symmetric = "symmetric" # 是否对称
    Judge = "judge" # 判断条件

class Rule(element.Element):
    """推理规则
    """

    def translate(self, lang, require = None, **kwargs):
        return super().translate(lang, require, **kwargs)

    def _get_relation_conclusion(self, props: Sequence[prop.Proposition], symmetric_execute: bool = False) -> list[prop.Proposition]:
        """当推理规则的类型为relation时，根据条件推理结论

        Args:
            props (Sequence[prop.Proposition]): 条件
            symmetric_execute (bool, optional): 是否处于对称执行状态，默认为False.

        Returns:
            list[prop.Proposition]: 结论
        """
        results: list[prop.Proposition] = []
        condition_dict: dict = self[RuleField.Condition] if not symmetric_execute else self[RuleField.Conclusion]
        conclusion_dict: dict = self[RuleField.Conclusion] if not symmetric_execute else self[RuleField.Condition]
        curr_prop = props[0]
        if curr_prop.kind != condition_dict['kind']:
            if self[RuleField.Symmetric] and not symmetric_execute:
                return self._get_relation_conclusion(props, symmetric_execute=True)
            return results
        attrs: list[str] = condition_dict['attrs']
        for attr in attrs:
            if not curr_prop.has_attr(attr):
                return results
        res_prop = prop.Proposition(kind=conclusion_dict['kind'])
        condition_attrs: list[str] = condition_dict['attrs']
        conclusion_attrs: list[str] = conclusion_dict['attrs']
        for attr1, attr2 in zip(condition_attrs, conclusion_attrs):
            res_prop[attr2] = curr_prop[attr1]
        results.append(res_prop)
        return results

    def _get_rule_conclusion(self, props: Sequence[prop.Proposition]) -> list[prop.Proposition]:
        """当推理规则的类型为rule时，根据条件推理结论

        Args:
            props (Sequence[prop.Proposition]): 条件

        Returns:
            list[prop.Proposition]: 结论

        Raises:
            ValueError: 当执行注入语句出现错误时
        """
        results: list[prop.Proposition] = []
        condition_dicts: list[dict] = self[RuleField.Condition]
        conclusion_dicts: list[dict] = self[RuleField.Conclusion]
        for p, c in zip(props, condition_dicts):
            # 如果输入的类型不满足条件要求的类型，则返回空列表
            if p.kind != c['kind']:
                return results
            # 如果输入的属性不满足条件要求的属性，则返回空列表
            attrs: list[str] = c['attrs']
            for attr in attrs:
                if not p.has_attr(attr):
                    return results
            # 利用exec()函数执行定义语句
            sentence = f"{c['name']} = p"
            try:
                exec(sentence)
            except Exception as e:
                raise ValueError(f"执行语句'{sentence}'时出现错误: {e}")
        for c in conclusion_dicts:
            conclusion = prop.Proposition(kind=c['kind'])
            attrs: dict[str, str] = c['attrs']
            for attr, code in attrs.items():
                sentence = f"conclusion.{attr} = {code}"
                try:
                    exec(sentence)
                except Exception as e:
                    raise ValueError(f"执行语句'{sentence}'时出现错误: {e}")
            results.append(conclusion)
        return results

    def reason(self, props: Sequence[prop.Proposition]) -> list[graph.Node]:
        """根据规则推理新的命题

        Args:
            props (Sequence[prop.Proposition]): 命题序列

        Returns:
            list[graph.Node]: 推理得到的新命题
        """
        num_of_conditions = len(self[RuleField.Condition])
        desc = f"使用推理规则{self.name}进行推理"
        total = math.perm(len(props), num_of_conditions)
        results: list[graph.Node] = []
        for curr_props in tqdm(permutations(props, num_of_conditions), desc=desc, total=total):
            if self.kind == RuleType.Rule:
                curr_conclusions = self._get_rule_conclusion(curr_props)
            elif self.kind == RuleType.Relation:
                curr_conclusions = self._get_relation_conclusion(curr_props)
            else:
                raise ValueError(f"不支持的规则类型{self.kind}")
            if len(curr_conclusions) > 0:
                for con in curr_conclusions:
                    if not con.is_contained(props):
                        node_dict = {graph.NodeField.Condition: list(curr_props), graph.NodeField.Conclusion: con, graph.NodeField.Rule: self}
                        results.append(graph.Node(node_dict))
        return results