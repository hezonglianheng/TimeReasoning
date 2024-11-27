# encoding: utf8
# date: 2024-09-04
# author: Qin Yuhang
"""
关于推理场景的基本定义和基本操作
"""
import abc
from copy import deepcopy
import random
from typing import Union, Any, Dict, Literal, Optional
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop
import proposition.relation as relation
import proposition.rule as rule
from proposition.machines import ReasonMachine as RM
from proposition.machines import SearchMachine as SM
from proposition.machines import AnswerMachine as AM
from proposition.config import SEMICOLON, COLON  # 引入标点符号用于串联表达
from proposition.graph import Graph
from proposition.machines import GetRangeMachine as GRM
import proposition.machines as machines
from proposition.machines import AskAllMachine

class Scene(metaclass=abc.ABCMeta):
    """
    推理场景的抽象类\n
    用于定义推理场景的基本属性和操作
    """

    def __init__(self, guide: str = "", *, ask_mode: Literal['random', 'deepest', 'tag'] = 'random', tag: Optional[list[str]] = None, lang: str = "zh") -> None:
        """初始化推理场景
        Args:
            guide (str, optional): 引导语. 默认为空字符串.
            ask_mode (Literal['random', 'deepest'], optional): 提问模式. 默认为'random'.可选的值有：
                - 'random'，即随机提问. 
                - 'deepest'，优先提问最深层的命题.
                - 'tag'，根据命题的标签进行提问，该模式需要传入tag参数(一个标签列表).
            tag (Optional[list[str]], optional): 提问标签. 默认为None.
            lang (str, optional): 语言. 默认为"zh"(简体中文).
        """
        self.guide = guide  # 引导语
        self.ask_mode = ask_mode  # 提问模式
        self.tag = tag # 提问标签
        self.lang = lang  # 语言
        self.relations: list[relation.Relation] = []  # 关系列表
        self.rules: list[rule.Rule] = []  # 规则列表
        self.temps: dict[str, list[str]] = []  # 模板字典
        # 命题收集变量
        self._init_props: list[prop.Proposition] = []
        self._all_props: list[prop.Proposition] = []
        self._chosen_group: list[prop.Proposition] = []
        self._statements: list[str] = []
        self._asked_prop: prop.Proposition = None
        self._ask_info: dict[str, Any] = {}
        self._value_range: dict[str, list[Any]] = dict()
        self._knowledges: list[prop.Proposition] = []
        self.graph: Graph = None
        self.chain: str = ""
        self._reachables: list[prop.Proposition] = [] # 可达命题列表
        # 11-25新增：场景的范围获取机
        self._range_machine: GRM = None # 范围获取机
        # 11-26新增：场景的询问机
        self._ask_all_machine: AskAllMachine = None
        self._ask_correct: bool = True

    def add_knowledge(self, number: int = 5, seed: Union[int, float, None] = None,
                      file_path: Union[str, Path, None] = None) -> None:
        """添加知识命题
        Args:
            number (int): 要添加的知识命题数量. 默认为5.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            file_path (Union[str, Path, None], optional): 知识命题文件路径. 默认为None.
        """
        assert number > 0, "知识命题数量必须大于0"
        random.seed(seed)
        print(f"开始添加知识命题.共添加{number}个.")

    def get_all_props(self) -> None:
        """获得场景的全部命题"""
        assert len(self._init_props) >= 2, "命题数量必须大于等于2"
        print("开始生成全部命题！")
        curr_props = deepcopy(self._init_props)
        knowledge = deepcopy(self._knowledges)
        rm = RM(curr_props, self.relations, self.rules, knowledge)
        self._all_props = rm.run()
        print(f"全部命题生成完毕！生成了{len(self._all_props)}个命题")

    @abc.abstractmethod
    def get_all_groups(self) -> None:
        """调用搜索机，以发现可行的陈述命题组合\n
        之后，该方法从可行的陈述命题组合出发，建立推理图，获得可达命题列表\n
        最后，该方法初始化范围获取机.\n
        注意：该方法需要被子类重写
        """
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始搜索一组可行的命题组合.")
        knowledge = deepcopy(self._knowledges)
        sm = SM(self._init_props, self._all_props, self.relations, self.rules, knowledge)
        self._chosen_group = sm.run()
        print(f"命题组合搜索结束.")
        print(f"获取推理图.")
        rm = RM(deepcopy(self._chosen_group), self.relations, self.rules, deepcopy(self._knowledges),
                graph_construct=True)

        self._reachables = rm.run()  # 11-12修改: 将建立推理图得到的命题加入可达命题列表
        self.graph = rm.graph
        print(f"推理图获取完毕.")
        # 11-25新增：初始化范围获取机
        self._range_machine = GRM(self._all_props)
        print("初始化选取干扰项的范围获取机.")
        # 11-26新增：初始化询问机
        self._ask_all_machine = AskAllMachine(deepcopy(self._reachables), deepcopy(self._chosen_group), self.temps, self.graph, self._range_machine, ask_correct=self._ask_correct, lang=self.lang, ask_mode=self.ask_mode, tag=self.tag)
        print("初始化询问机.")

    def get_statements(self) -> list[str]:
        """获取一组命题组合的全部陈述
        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        Returns:
            list[str]: 一组命题组合的全部陈述
        """
        # assert len(self._all_groups) > 0, "必须先获取可以表述全部情形的命题组合"
        # random.seed(seed)
        # idxs = random.choice(self._all_groups) # 选择一组命题
        # self._chosen_group = [self._all_props[i] for i in idxs] # 选中的命题组合
        self._statements = [i.state(self.temps) for i in self._chosen_group]  # 陈述列表
        print("得到随机选择一组命题的陈述.")
        return self._statements
    
    # @abc.abstractmethod
    def ask_one(self, seed: Union[int, float, None] = None) -> Dict[str, Any]:
        """随机选择一个命题，提问，并根据具体情况获得备选项，最后返回问题信息
        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        Returns:
            Dict[str, Any]: 问题信息
        """
        # 修改：选择的命题需要是未进入描述的命题
        # 修改：提问的命题需要是可提问的命题
        print("随机选择一个未进入描述的命题，提问.")

        # 11-24更新：修改提问方式，以支持提问最深层命题和按照标签提问
        if self.ask_mode == 'random':
            candidates: list[prop.Proposition] = [i for i in self._reachables if not i.got(self._chosen_group) and i.askable]
            # self._asked_prop = random.choice([i for i in self._reachables if not i.got(self._chosen_group) and i.askable])
        elif self.ask_mode == 'deepest':
            assert self.graph is not None, "deepest提问模式下，必须先获取推理图"
            deepest_layer: int = -1
            for i in [k for k in self._reachables if not k.got(self._chosen_group) and k.askable]:
                layer = self.graph.layer_query(i)
                if layer > deepest_layer:
                    deepest_layer = layer
            candidates = [i for i in self._reachables if not i.got(self._chosen_group) and i.askable and self.graph.layer_query(i) == deepest_layer]
            # self._asked_prop = random.choice(self.graph.deepest_layer_props)
        elif self.ask_mode == 'tag':
            assert self.tag is not None, "tag提问模式下，提问标签不能为空"
            candidates = [i for i in self._reachables if not i.got(self._chosen_group) and i.askable and i.typetag in self.tag]
            # self._asked_prop = random.choice([i for i in self._reachables if not i.got(self._chosen_group) and i.askable and i.typetag in self.tag])
        else:
            raise ValueError(f"提问模式错误，不存在{self.ask_mode}模式")
        if len(candidates) == 0:
            print("没有可提问的命题，跳过.")
            return None
        self._asked_prop = random.choice(candidates)
        # self._asked_prop = random.choice([i for i in self._all_props if not i.got(self._chosen_group) and i.askable])
        self._ask_info = self._asked_prop.ask(self.temps)
        print("提问完毕.")
        return self._ask_info

    def set_value_range(self) -> None:
        """设置命题的值范围
        """
        if self._asked_prop is None:
            return None # 如果没有可提问的命题，直接返回None
        typ: str = self._ask_info.get(prop.TYPE)
        assert typ is not None, "提问信息中没有类型信息"
        self._value_range[typ] = self._range_machine.get_range(self._ask_info)

    def get_answers(self, seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1) -> Dict[str, Any]:
        """获取选项和正确答案
        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            options (int, optional): 选项数量. 默认为4.
            all_wrong_prob (float, optional): 全部错误选项的概率. 默认为0.1.
        Returns:
            Dict[str, Any]: 答案信息
        """
        # assert self._asked_prop is not None, "必须先执行ask()方法进行提问"
        if self._asked_prop is None:
            return None # 11-24更新：如果没有可提问的命题，直接返回None

        # am = AM(self._all_props, self._asked_prop, self._ask_info, seed, options, all_wrong_prob)
        am = AM(self._reachables, self._asked_prop, self._ask_info, seed, options, all_wrong_prob)
        for k, v in self._value_range.items():
            am.set_value_range(k, v)
        return am.run()

    def get_chain(self, ans_prop: list[prop.Proposition]) -> str:
        """获取推理链

        Args:
            ans_prop (list[prop.Proposition]): 答案命题，是由回答机返回的答案命题列表

        Returns:
            str: 推理链
        """
        assert self._asked_prop is not None, "必须先执行ask()方法进行提问"

        reason_path = self.graph.backtrace(self._asked_prop)
        for i in ans_prop:
            if i != self._asked_prop:
                reason_path = reason_path + self.graph.backtrace(i)

        self.chain = "\n".join([i.state(self.temps, lang=self.lang) for i in reason_path])
        return self.chain

    def ask_all(self, seed: Union[int, float, None] = None) -> dict[str, Any] | None:
        """询问“以下说法正确的是”“以下说法错误的是”这样的问题的函数

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            dict[str, Any]: 问题信息
        """
        assert self._ask_all_machine is not None, "必须先初始化询问机"
        return self._ask_all_machine.run()
    
    def run(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        """运行场景，获取一组题目
        Args:
            execute (int, optional): 生成的题目数量. 默认为10.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            list[dict[str, Any]]: 一组题目
        """
        self.get_all_props()
        question_list = []
        i = 0
        while len(question_list) < execute:
            i += 1
            print(f"开始第{i}次获取.")
            self.get_all_groups()
            self.get_statements()
            self.ask_one(seed)
            self.set_value_range() # 设置值域
            answers = self.get_answers(seed)
            if answers is None:
                print("未能获取答案，跳过.")
                continue
            # 修改：先判定能否生成答案，再获取推理链
            ans_prop = answers[machines.ANSWERPROP] # 将正确答案填入空中的命题
            chain = self.get_chain(ans_prop)
            text = self.guide + COLON + SEMICOLON.join(self._statements)  # 题面文本，由引导语和陈述组成
            # 问题信息
            item = {
                        "guide": self.guide, 
                        "statement": self._statements, 
                        "text": text,
                        "question": self._ask_info[prop.SENTENCE], 
                        "options": answers[machines.OPTIONS], 
                        "answers": answers[machines.ANSWERS], 
                        "chain": chain, 
                        # 11-24更新：增加提问命题的层级信息
                        "layer": self.graph.layer_query(self._asked_prop), 
                        # 11-24更新：增加提问命题的标签信息
                        "tag": self._asked_prop.typetag
                    }
            question_list.append(item)
        print(f"获取题目{i}次，获得题目{len(question_list)}个.")
        return question_list

    def run_ask_all(self, execute: int = 10, seed: Union[int, float, None] = None, ask_correct: bool = True) -> list[dict[str, Any]]:
        """运行场景，获取一组询问多个命题类型的题目
        Args:
            execute (int, optional): 生成的题目数量. 默认为10.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            ask_correct (bool, optional): 询问机的询问模式. 默认为True(询问“以下说法正确的是”). 可选的值有：
                - True，询问“以下说法正确的是”
                - False，询问“以下说法错误的是”

        Returns:
            list[dict[str, Any]]: 一组题目
        """
        random.seed(seed)
        self._ask_correct = ask_correct # 设置询问机的询问模式
        self.get_all_props()
        question_list = []
        i = 0
        while len(question_list) < execute:
            i += 1
            print(f"开始第{i}次获取.")
            self.get_all_groups()
            self.get_statements()
            ask_all_info = self.ask_all(seed)
            if ask_all_info is None:
                print("未能获取答案，跳过.")
                continue
            text = self.guide + COLON + SEMICOLON.join(self._statements)  # 题面文本，由引导语和陈述组成
            item = {
                "guide": self.guide,
                "statement": self._statements,
                "text": text,
            } | ask_all_info
            question_list.append(item)
        print(f"获取题目{i}次，获得题目{len(question_list)}个.")
        return question_list