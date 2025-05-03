# encoding: utf8
# date: 2025-03-02

"""命题推理使用的推理规则
"""

import element
import config
import represent # 为保证exec()函数的执行，需要引入represent模块
import event # 为保证exec()函数的执行，需要引入event模块
import proposition as prop
import mynode
import json5
from tqdm import tqdm
from itertools import product, permutations
from collections.abc import Sequence
import warnings
from functools import reduce
from copy import deepcopy

# constants.
KIND = "kind"
ATTRS = "attrs"
# rule types.
RULE = "rule"
RELATION = "relation"
# rule fields.
CONDITION = "condition"
CONCLUSION = "conclusion"
SYMMETRIC = "symmetric"
JUDGE = "judge"

class Rule(element.Element):
    """推理规则
    """

    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        assert self.has_attr(CONDITION), f"推理规则{name}缺少条件字段"
        assert self.has_attr(JUDGE), f"推理规则{name}缺少判断方式字段"
        assert self.has_attr(CONCLUSION), f"推理规则{name}缺少结论字段"
        self[SYMMETRIC] = kwargs.get(SYMMETRIC, False)

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
        condition_dict: dict = self[CONDITION] if not symmetric_execute else self[CONCLUSION]
        conclusion_dict: dict = self[CONCLUSION] if not symmetric_execute else self[CONDITION]
        curr_prop = props[0]
        # 05-03增加：如果curr_prop不可被提问，则不进行推理
        if not curr_prop[prop.ASKABLE]:
            return results
        # 条件是否满足规则
        if curr_prop.kind != condition_dict[KIND]:
            if self[SYMMETRIC] and not symmetric_execute:
                return self._get_relation_conclusion(props, symmetric_execute=True)
            return results
        attrs: list[str] = condition_dict[ATTRS]
        for attr in attrs:
            if not curr_prop.has_attr(attr):
                return results
        # 判断规则是否可以使用
        judge_dict: list[str] = self[JUDGE]
        for judge in judge_dict:
            judge_res: bool = eval(judge)
            if not judge_res:
                return results
        # 获取结论
        res_prop = prop.Proposition(kind=conclusion_dict[KIND])
        condition_attrs: list[str] = condition_dict[ATTRS]
        conclusion_attrs: list[str] = conclusion_dict[ATTRS]
        for attr1, attr2 in zip(condition_attrs, conclusion_attrs):
            res_prop[attr2] = curr_prop[attr1]
        # 05-03增加：结论命题继承条件命题的askable属性
        res_prop[prop.ASKABLE] = curr_prop[prop.ASKABLE]
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
        # 05-03增加：计算可提问性，如果props都不可被提问，则不进行推理
        askable = any([p[prop.ASKABLE] for p in props])
        if not askable:
            return results
        condition_dicts: list[dict] = self[CONDITION]
        conclusion_dicts: list[dict] = self[CONCLUSION]
        # 条件是否符合规则
        for p, c in zip(props, condition_dicts):
            # 如果输入的类型不满足条件要求的类型，则返回空列表
            if p.kind != c[KIND]:
                return results
            # 如果输入的属性不满足条件要求的属性，则返回空列表
            attrs: list[str] = c[ATTRS]
            for attr in attrs:
                if not p.has_attr(attr):
                    return results
            # 利用exec()函数执行定义语句
            sentence = f"{c['name']} = p"
            exec(sentence)
        # 判断规则是否可以使用
        judge_dict: list[str] = self[JUDGE]
        for judge in judge_dict:
            judge_res: bool = eval(judge)
            if not judge_res:
                return results
        # 获取结论
        for c in conclusion_dicts:
            conclusion = prop.Proposition(kind=c[KIND])
            attrs: dict[str, str] = c[ATTRS]
            for attr, code in attrs.items():
                sentence = f"conclusion['{attr}'] = {code}"
                exec(sentence)
            # 05-03增加：结论命题继承条件命题的askable属性
            conclusion[prop.ASKABLE] = askable
            results.append(conclusion)
        return results

    def reason(self, old_props: list[prop.Proposition], new_props: list[prop.Proposition], reason_round: int) -> list[mynode.Node]:
        """根据规则推理新的命题

        Args:
            old_props (list[prop.Proposition]): 旧命题列表
            new_props (list[prop.Proposition]): 新命题列表
            reason_round (int): 推理的轮次

        Returns:
            list[mynode.Node]: 推理得到的新命题节点
        """
        used_props = deepcopy(old_props)
        all_prop: list[prop.Proposition] = [p for p in old_props] + [p for p in new_props]
        con_prop_lists: list[list[prop.Proposition]] = []
        if self.kind == RULE:
            con_kinds: list[str] = [c[KIND] for c in self[CONDITION]]
            con_props = [[p for p in all_prop if p.kind == kind] for kind in con_kinds]
            con_prop_lists.extend(con_props)
        elif self.kind == RELATION:
            con_kind: str = self[CONDITION][KIND]
            con_props = [p for p in all_prop if p.kind == con_kind]
            con_prop_lists.append(con_props)
        else:
            raise ValueError(f"推理规则{self.name}具有不支持的规则类型{self.kind}")
        results: list[mynode.Node] = []
        total = reduce(lambda x, y: x*y, [len(i) for i in con_prop_lists])
        for curr_props in tqdm(product(*con_prop_lists), total=total, desc=f"第{reason_round}轮推理使用推理规则{self.name}"):
            if all([p in used_props for p in curr_props]):
                continue
            if len(curr_props) > 1 and any(p1 == p2 for p1, p2 in permutations(curr_props, r=2)):
                continue
            if self.kind == RULE:
                curr_conclusions = self._get_rule_conclusion(curr_props)
            elif self.kind == RELATION:
                curr_conclusions = self._get_relation_conclusion(curr_props)
            else:
                raise ValueError(f"推理规则{self.name}具有不支持的规则类型{self.kind}")
            if len(curr_conclusions) > 0:
                for con in curr_conclusions:
                    node_dict = {mynode.CONDITION: list(curr_props), mynode.CONCLUSION: con, mynode.RULE: self}
                    results.append(mynode.Node(**node_dict))
        return results

def get_reasoning_rules(rule_names: Sequence[str]) -> list[Rule]:
    """根据选择的推理规则名称，获取推理规则

    Args:
        rule_names (Sequence[str]): 选择的推理规则名称

    Returns:
        list[Rule]: 推理规则

    Raises:
        ValueError: 当推理规则的名字重复时
    """
    with config.RULE_FILE.open("r", encoding="utf-8") as f:
        data: dict = json5.load(f)
    rule_dicts: list[dict] = data["rules"]
    # 自检：推理规则的名字不能相同
    rules: list[Rule] = [Rule(**rule_dict) for rule_dict in rule_dicts]
    assert element.name_is_unique(rules), "推理规则的名字不能相同"
    # 根据名称获取推理规则
    res_rules: list[Rule] = []
    for name in rule_names:
        name_rules = [rule for rule in rules if rule.name == name]
        if len(name_rules) == 0:
            warnings.warn(f"要引用的推理规则{name}不存在", UserWarning)
        else:
            res_rules.extend(name_rules)
    return res_rules