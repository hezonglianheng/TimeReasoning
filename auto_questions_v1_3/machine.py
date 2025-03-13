# encoding: utf8
# date: 2025-03-07

"""提供用于时间推理题制作的机器类
"""

import config
import event
import graph
import proposition as prop
import json5
from tqdm import tqdm
import random
from typing import Literal

# constants.
CHOOSE_RULE = "choose_rule"

class PropChooseMachine:
    """用于时间推理题已知条件选择的机器类
    """
    def __init__(self, sorted_events: list[event.Event], graph: graph.ReasoningGraph):
        """初始化命题选择器

        Args:
            sorted_events (list[event.Event]): 已按照时间顺序排序的事件列表
            graph (graph.ReasoningGraph): 推理图
        """
        self.sorted_events = sorted_events
        self.graph = graph
        self.all_props = self.graph.get_all_props()
        self.choose_rule: dict[str, list[dict[str, str]]] = {}
        with open(config.PROP_CHOOSE_RULE_FILE, "r", encoding = "utf8") as f:
            self.choose_rule = json5.load(f)[CHOOSE_RULE]

    def _choose_prop(self, e: event.Event) -> prop.Proposition:
        """根据输入的事件选择命题

        Args:
            e (event.Event): 输入的事件

        Raises:
            ValueError: 输入的事件具有未知的类型

        Returns:
            prop.Proposition: 随机选择可以表示这一事件的命题
        """
        candidate_props: list[prop.Proposition] = []
        if e.kind not in self.choose_rule:
            raise ValueError(f"输入的事件具有未知的类型：{e.kind}")
        for rule in self.choose_rule[e.kind]:
            temp_props = list(filter(lambda x: x.kind == rule["kind"], self.all_props))
            temp_props = list(filter(lambda x: e == x[rule["attr"]], temp_props))
            candidate_props.extend(temp_props)
        chosen_prop = random.choice(candidate_props)
        return chosen_prop

    def run(self) -> list[prop.Proposition]:
        """运行命题选择器，选择命题

        Raises:
            ValueError: 未知事件类型
            ValueError: 未知的命题选择策略

        Returns:
            list[prop.Proposition]: 选择的命题
        """
        chosen_props: list[prop.Proposition] = []
        for e in tqdm(self.sorted_events, desc=f"根据事件选择命题"):
            if e.kind == event.TEMPORAL:
                chosen_prop = self._choose_prop(e)
                chosen_props.append(chosen_prop)
            elif e.kind == event.DURATION:
                chosen_prop = self._choose_prop(e)
                chosen_props.append(chosen_prop)
            elif e.kind == event.FREQUENT:
                pass
            elif e.kind == event.DURATIVE:
                strategy: Literal['parent', 'children'] = random.choice(['parent', 'children'])
                if strategy == "parent":
                    chosen_prop = self._choose_prop(e)
                    chosen_props.append(chosen_prop)
                elif strategy == "children":
                    for child_name in [event.START_EVENT, event.END_EVENT, event.DURATION_EVENT]:
                        child = e[child_name]
                        chosen_prop = self._choose_prop(child)
                        chosen_props.append(chosen_prop)
                else:
                    raise ValueError(f"未知的命题选择策略：{strategy}")
            else:
                raise ValueError(f"未知事件类型：{e.kind}")
        print(f"根据事件选择了{len(chosen_props)}个命题作为已知命题")
        return chosen_props