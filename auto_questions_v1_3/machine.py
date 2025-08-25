# encoding: utf8
# date: 2025-03-07

"""提供用于时间推理题制作的机器类
"""

import config
import element
import event
import graph
import proposition as prop
import json5
from tqdm import tqdm
import random
from typing import Literal, Optional, Any
import copy
from string import ascii_uppercase
from collections import defaultdict
from functools import reduce

# constants.
CHOOSE_RULE = "choose_rule"
ALL_WRONG_PROB = .1 # 设置“所有选项均不符合要求”的概率

# 提问信息
QUESTION = "question"
ASK_ATTR = "ask_attr"
OPTIONS = "options"
ANSWER = "answer"
# 05-02新增：增加获得提问命题的推理链长度
COT_LENGTH = "cot_length"
"""获得提问命题的推理链长度"""

class PropChooseMachine:
    """时间推理题已知命题选择器
    """
    def __init__(self, sorted_events: list[event.Event], g: graph.ReasoningGraph):
        """初始化命题选择器

        Args:
            sorted_events (list[event.Event]): 已按照时间顺序排序的事件列表
            graph (graph.ReasoningGraph): 推理图
        """
        self.sorted_events = sorted_events
        self.graph = g
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
        # 08-23增加：增加对被选择命题的输出
        chosen_props_trans = [i.translate(lang=config.CHINESE) for i in chosen_props]
        print(f"根据事件选择了{len(chosen_props)}个命题作为已知命题", *chosen_props_trans, sep="\n")
        return chosen_props

class OptionGenerator:
    """选项生成器
    """
    def __init__(self, g: graph.ReasoningGraph):
        """初始化选项生成器

        Args:
            g (graph.ReasoningGraph): 推理图
        """
        self.graph = g
        """推理图"""
        self.reachable_props = g.get_reachable_props()
        """选项选取时可达的命题"""
        self.attr_range: dict[str, dict[str, list[element.Element]]] = defaultdict(dict)
        """不同命题类型、不同属性值的可选值域范围"""

    def set_attr_range(self, prop_kind: str, attr: str, attr_range: list[element.Element]):
        """设置属性值的可选值域范围

        Args:
            prop_kind (str): 命题类型
            attr (str): 属性名称
            attr_range (list[element.Element]): 可选值域范围
        """
        self.attr_range[prop_kind][attr] = attr_range

    def get_element_options(self, asked_prop: prop.Proposition, ask_attr: str, num: int = 1, correct_num: Optional[int] = None, **kwargs) -> list[tuple[element.Element, bool]]:
        """从命题和属性的可选值域范围中选择一定量的元素

        Args:
            asked_prop (prop.Proposition): 被询问的命题
            ask_attr (str): 被询问的属性
            num (int, optional): 选择的元素数量. 默认为1.
            correct_num (Optional[int], optional): 正确元素的数量. 默认为None(此时不指定元素的正确性).

        Raises:
            ValueError: 可选值域范围数量少于备选数量

        Returns:
            list[tuple[element.Element, bool]]: 选择的元素列表，以及这些元素对应的正确性
        """
        ask_kind = asked_prop.kind
        if ask_kind in self.attr_range and ask_attr in self.attr_range[ask_kind]:
            temp_range = self.attr_range[ask_kind][ask_attr]
        else:
            temp_range: list[element.Element] = []
            for p in filter(lambda x: x.kind == ask_kind, self.reachable_props):
                temp_element: element.Element = p[ask_attr]
                if not temp_element.is_contained(temp_range):
                    temp_range.append(temp_element)
        # 06-20修改：需要排除的是命题中所有已经出现过的属性值
        temp_range = [i for i in temp_range if not i.is_contained(asked_prop.all_attr_elements())] # 需要排除被提问的命题中已有的属性值
        if len(temp_range) < num:
            raise ValueError(f"可选值域范围不足，只有{len(temp_range)}个元素，少于{num}个")
        res_list: list[tuple[element.Element, bool]] = []
        if correct_num is None:
            samples = random.sample(temp_range, num)
            for s in samples:
                new_prop = copy.deepcopy(asked_prop)
                new_prop[ask_attr] = s
                res_list.append((s, new_prop.is_contained(self.reachable_props)))
        else:
            assert correct_num <= num, f"正确元素数量{correct_num}大于总元素数量{num}"
            # 06-20修改: element_judge的长度改为与temp_range的长度相同
            element_judge = [False] * len(temp_range)
            for i, t in enumerate(temp_range):
                new_prop = copy.deepcopy(asked_prop)
                new_prop[ask_attr] = t
                element_judge[i] = new_prop.is_contained(self.reachable_props)
            assert sum(element_judge) >= correct_num, f"正确元素数量{sum(element_judge)}小于要求的数量{correct_num}"
            assert sum([not i for i in element_judge]) >= num - correct_num, f"错误元素数量{sum([not i for i in element_judge])}小于要求的数量{num - correct_num}"
            true_elements = [i for i, j in zip(temp_range, element_judge) if j]
            false_elements = [i for i, j in zip(temp_range, element_judge) if not j]
            # 06-20修订：如果正确元素或错误元素数量为0或要求为0，则不进行采样
            if len(true_elements) == 0 or correct_num == 0:
                true_samples = []
            else:
                true_samples = random.sample(true_elements, correct_num)
            if len(false_elements) == 0 or (num - correct_num) == 0:
                false_samples = []
            else:
                false_samples = random.sample(false_elements, num - correct_num)
            res_list.extend([(s, True) for s in true_samples])
            res_list.extend([(s, False) for s in false_samples])
        return res_list

    def get_prop_option(self, asked_prop: prop.Proposition, ask_attr: str, be_correct: bool = True, **kwargs) -> prop.Proposition:
        """生成一个作为选项的待选的命题

        Args:
            asked_prop (prop.Proposition): 被提问的命题
            ask_attr (str): 被提问的属性
            be_correct (bool, optional): 是否是正确选项. 默认为True.

        Returns:
            prop.Proposition: 作为选项的命题
        """
        if be_correct:
            return asked_prop
        else:
            new_element = self.get_element_options(asked_prop, ask_attr, num = 1, correct_num = 0, **kwargs)[0][0]
            new_prop = copy.deepcopy(asked_prop)
            new_prop[ask_attr] = new_element
            return new_prop

class AllWrongOption(element.Element):
    """表示所有选项均不符合要求的选项
    """
    def translate(self, lang, require = None, **kwargs):
        return config.LANG_CONFIG[lang]["all_wrong"]

    def get_prop_difficulty(self) -> float:
        """获取命题的难度，值设为1.0

        Returns:
            float: 命题的难度
        """
        return 1.0

    def get_question_difficulty(self, lang: str) -> float:
        """获取问题的难度，值设为1.0

        Args:
            lang (str): 语言

        Returns:
            float: 问题的难度
        """

        return 1.0

    def get_prop_tag(self) -> str:
        """获取命题的标签

        Returns:
            str: 命题的标签
        """
        return ""

class CorStatQuestion(element.Element):
    """表示问题“以下选项中正确的是”
    """
    def translate(self, lang, require = None, **kwargs):
        return config.LANG_CONFIG[lang]["ask_right"]

class IncStatQuestion(element.Element):
    """表示问题“以下选项中不正确的是”
    """
    def translate(self, lang, require = None, **kwargs):
        return config.LANG_CONFIG[lang]["ask_wrong"]

class AskMachine:
    """提问机，根据推理图和选项生成器生成问题、选项、答案
    """
    def __init__(self, g: graph.ReasoningGraph, gen: OptionGenerator):
        self.graph = g
        """推理图"""
        self.option_generator = gen
        """选项生成器"""

    def _get_candidate_props(self, prop_type: Literal["random", "deepest", "certain"], **kwargs) -> list[prop.Proposition]:
        """根据命题候选方式，获取候选命题

        Args:
            prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;]): 命题选择方式
            
            - random: 随机选择命题
            - deepest: 选择最深的命题
            - certain: 选择某种类型的命题
            
            **kwargs: 其他参数

        Raises:
            ValueError: 未知的命题选择方式

        Returns:
            list[prop.Proposition]: 候选命题列表
        """
        if prop_type == "random":
            return self.graph.get_reachable_props(use_askable=True)
        elif prop_type == "deepest":
            return self.graph.get_deepest_conclusions(use_askable=True)
        elif prop_type == "certain":
            return [i for i in self.graph.get_reachable_props(use_askable=True) if i.kind == kwargs["kind"]]
        else:
            raise ValueError(f"未知的命题选择方式：{prop_type}")
    
    def _get_options_and_answer(self, options: list[tuple[element.Element, bool]]) -> tuple[dict[str, element.Element], list[str]]:
        """根据元素和元素的正误生成选项和答案

        Args:
            options (list[tuple[element.Element, bool]]): 元素和元素的正误列表

        Returns:
            tuple[dict[str, element.Element], list[str]]: 选项字典和答案列表
        """
        random.shuffle(options)
        options_dict = {ascii_uppercase[i]: options[i][0] for i in range(len(options))}
        answer_list = [option for option, (_, judge) in zip(options_dict, options) if judge]
        temp_prob = random.random()
        if temp_prob < ALL_WRONG_PROB:
            # 获得最后一个选项的选项字母
            last_option = ascii_uppercase[len(options_dict) - 1]
            options_dict[last_option] = AllWrongOption()
            if last_option in answer_list:
                answer_list.remove(last_option)
            if len(answer_list) == 0:
                answer_list.append(last_option)
        return options_dict, answer_list
    
    def precise_event(self, prop_type: Literal["random", "deepest", "certain"] = "random", option_num: int = 4, correct_num: Optional[int] = None, **kwargs) -> dict[str, Any]:
        """生成精确事件问题

        Args:
            prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;], optional): 命题选择方式. 默认为&quot;random&quot;.
            option_num (int, optional): 选项数量. 默认为4.
            correct_num (Optional[int], optional): 正确选项数量. 默认为None(不指定数量).

        Returns:
            dict[str, Any]: 问题、提问属性、选项、答案
        """
        candidate_props = self._get_candidate_props(prop_type, **kwargs)
        while True:
            try:
                asked_prop = random.choice(candidate_props)
                ask_attr = asked_prop.ask_attr()
                other_options = self.option_generator.get_element_options(asked_prop, ask_attr, option_num - 1, correct_num, **kwargs)
            except Exception as e:
                print(f"获取选项失败：{e}")
                continue
            break
        origin_element: element.Element = asked_prop[ask_attr]
        all_options = [(origin_element, True)] + other_options
        options_dict, answer_list = self._get_options_and_answer(all_options)
        # 08-23新增：增加对被提问命题的输出
        print(asked_prop.translate(lang=config.CHINESE), f"提问属性：{ask_attr}，属性值：{origin_element.translate(lang=config.CHINESE)}")
        print("选项：", [f"{k}: {v.translate(lang=config.CHINESE)}" for k, v in options_dict.items()])
        print("答案：", answer_list)
        # 05-02新增：增加获得提问命题的推理链
        cot = self.graph.backtrace(asked_prop)
        return {QUESTION: asked_prop, ASK_ATTR: ask_attr, OPTIONS: options_dict, ANSWER: answer_list, COT_LENGTH: len(cot)}

    def correct_statements(self, prop_type: Literal["random", "deepest", "certain"] = "random", option_num: int = 4, correct_num: Optional[int] = None, **kwargs) -> dict[str, Any]:
        """生成“以上选项正确的是”问题

        Args:
            prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;], optional): 命题选择方式. 默认为&quot;random&quot;.
            option_num (int, optional): 选项数量. 默认为4.
            correct_num (Optional[int], optional): 正确选项数量. 默认为None(不指定数量).

        Returns:
            dict[str, Any]: 问题、提问属性、选项、答案
        """
        temp_correct = correct_num if correct_num else random.randint(1, option_num)
        temp_judge = [True] * temp_correct + [False] * (option_num - temp_correct)
        random.shuffle(temp_judge)
        option_props: list[prop.Proposition] = []
        while True:
            try:
                candidate_props = self._get_candidate_props(prop_type, **kwargs)
                ask_props = random.sample(candidate_props, option_num)
                ask_attrs = [i.ask_attr() for i in ask_props]
                for i in range(option_num):
                    option_props.append(self.option_generator.get_prop_option(ask_props[i], ask_attrs[i], temp_judge[i], **kwargs))
            except Exception as e:
                print(f"获取选项失败：{e}")
                continue
            break
        options_dict, answer_list = self._get_options_and_answer([(i, j) for i, j in zip(option_props, temp_judge)])
        # 05-04新增：判断最后一个选项是否为all_wrong，如果是，需要backtrace的命题移除最后一个；否则需要backtrace的命题为所有选项
        if isinstance(option_props[option_num - 1], AllWrongOption):
            backtrace_props = ask_props[:-1]
        else:
            backtrace_props = ask_props
        # 08-23新增：增加对被选择命题的输出
        print("被选择命题：", [i.translate(lang=config.CHINESE) for i in options_dict.values()])
        print("答案：", answer_list)
        # 05-02新增：增加获得提问命题的推理链
        cots = [self.graph.backtrace(i) for i in backtrace_props]
        cot_length = reduce(lambda x, y: x + y, [len(i) for i in cots])
        return {QUESTION: CorStatQuestion(), ASK_ATTR: "", OPTIONS: options_dict, ANSWER: answer_list, COT_LENGTH: cot_length}

    def incorrect_statements(self, prop_type: Literal["random", "deepest", "certain"] = "random", option_num: int = 4, correct_num: Optional[int] = None, **kwargs) -> dict[str, Any]:
        """生成“以上选项不正确的是”问题

        Args:
            prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;], optional): 命题选择方式. 默认为&quot;random&quot;.
            option_num (int, optional): 选项数量. 默认为4.
            correct_num (Optional[int], optional): 正确选项数量. 默认为None(不指定数量).

        Returns:
            dict[str, Any]: 问题、提问属性、选项、答案
        """
        temp_correct = correct_num if correct_num else random.randint(1, option_num)
        temp_judge = [True] * temp_correct + [False] * (option_num - temp_correct)
        random.shuffle(temp_judge)
        option_props: list[prop.Proposition] = []
        while True:
            try:
                candidate_props = self._get_candidate_props(prop_type, **kwargs)
                ask_props = random.sample(candidate_props, option_num)
                ask_attrs = [i.ask_attr() for i in ask_props]
                for i in range(option_num):
                    option_props.append(self.option_generator.get_prop_option(ask_props[i], ask_attrs[i], (not temp_judge[i]), **kwargs))
            except Exception as e:
                print(f"获取选项失败：{e}")
                continue
            break
        options_dict, answer_list = self._get_options_and_answer([(i, j) for i, j in zip(option_props, temp_judge)])
        # 05-04新增：判断最后一个选项是否为all_wrong，如果是，需要backtrace的命题移除最后一个；否则需要backtrace的命题为所有选项
        if isinstance(option_props[option_num - 1], AllWrongOption):
            backtrace_props = ask_props[:-1]
        else:
            backtrace_props = ask_props
        # 08-23新增：增加对被选择命题的输出
        print("被选择命题：", [i.translate(lang=config.CHINESE) for i in options_dict.values()])
        print("答案：", answer_list)
        # 05-02新增：增加获得提问命题的推理链
        cots = [self.graph.backtrace(i) for i in backtrace_props]
        cot_length = reduce(lambda x, y: x + y, [len(i) for i in cots])
        return {QUESTION: IncStatQuestion(), ASK_ATTR: "", OPTIONS: options_dict, ANSWER: answer_list, COT_LENGTH: cot_length}

    def run(self, prop_type: Literal["random", "deepest", "certain"] = "random", question_type: Literal["precise", "correct", "incorrect"] = "precise", option_num: int = 4, correct_num: Optional[int] = None, **kwargs) -> dict[str, Any]:
        """运行提问机，提问

        Args:
            prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;], optional): 命题选择方式，默认为&quot;random&quot;.
            question_type (Literal[&quot;precise&quot;, &quot;correct&quot;, &quot;incorrect&quot;], optional): 试题类型，默认为&quot;precise&quot;.
            option_num (int, optional): 选项数量，默认为4.
            correct_num (Optional[int], optional): 正确选项数量，默认为None.

        Raises:
            ValueError: 未知的问题类型

        Returns:
            dict[str, Any]: 问题、提问属性、选项、答案
        """
        print(f"开始提问...")
        if question_type == "precise":
            res = self.precise_event(prop_type, option_num, correct_num, **kwargs)
        elif question_type == "correct":
            res = self.correct_statements(prop_type, option_num, correct_num, **kwargs)
        elif question_type == "incorrect":
            res = self.incorrect_statements(prop_type, option_num, correct_num, **kwargs)
        else:
            raise ValueError(f"未知的问题类型：{question_type}")
        print(f"提问完毕，获得问题信息.")
        return res