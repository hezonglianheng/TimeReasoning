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
# 11-30新增：引入难度评级函数
from proposition.level import ask_level

# constants.
LEVEL = "level"
CHAIN_LENGTH = "chain_length"
INIT_NUM = "init_num"
KNOWLEDGE_NUM = "knowledge_num"
SCENE_TYPE = "scene_type"

class Scene(metaclass=abc.ABCMeta):
    """
    推理场景的抽象类\n
    用于定义推理场景的基本属性和操作
    """
    # 11-30新增：场景的难度评级
    # 1-31修改：移动到内部
    # scene_level: float = 0.0  # 场景难度

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
        self._init_props: list[prop.Proposition] = [] # 初始命题
        self._all_props: list[prop.Proposition] = [] # 遍历推理得到的所有命题
        self._chosen_group: list[prop.Proposition] = [] # 被选择用于陈述的命题
        self._statements: list[str] = [] # 题目的陈述文本
        self._asked_prop: prop.Proposition = None # 被询问的命题
        self._ask_info: dict[str, Any] = {} # 从被询问的命题中获取的信息
        self._value_range: dict[str, list[Any]] = dict() # 不同的类型对应的值域
        self._knowledges: list[prop.Proposition] = [] # 知识命题
        self.graph: Graph = None # 推理图
        self.chain: str = "" # 推理链文本
        self._reachables: list[prop.Proposition] = [] # 可达命题列表
        # 11-25新增：场景的范围获取机
        self._range_machine: GRM = None # 范围获取机
        # 11-26新增：场景的询问机
        self._ask_all_machine: AskAllMachine = None
        self._ask_correct: bool = True # 是否询问“以下正确”，True为询问“以下正确”，False为询问“以下错误”
        # 11-30新增：推理链长度记录变量
        self.chain_length: int = 0
        # 12-01新增：记录由回答机返回的回答命题
        self.ans_props: list[prop.Proposition] = []
        # 12-11新增：记录由回答机返回的答案信息
        self.answer_info: dict[str, Any] = {}
        # 1-15新增：增加对问题中命题的难度的记录
        # 1-28修改：数据类型改为float
        self._question_difficulties: float = 0.0
        # 1-15新增：增加对已知条件中命题的难度的记录
        # 1-29修改：修改数据类型，改为平均值
        self._statement_difficulties: float = 0.0
        # 1-20新增：记录知识的难度
        self._knowledge_difficulties: int = 0
        self.scene_level: float = 0.0  # 场景难度

    # 12-13新增：场景类型名称
    @property
    @abc.abstractmethod
    def scene_type(self) -> str:
        """场景类型名称"""
        return ""
    
    # 12-24移动：将reset()方法移动到父类中，成为场景类的共同方法
    def reset(self):
        """清空场景中的初始化命题和知识命题"""
        self._init_props.clear()
        # 12-24新增：同时移除知识
        self._knowledges.clear()
        # 1-15新增：同时移除难度
        self._question_difficulties = 0.0
        # 1-20新增：同时移除知识难度
        self._knowledge_difficulties = 0
        # 2-5新增：移除命题难度
        self._statement_difficulties = 0.0
    
    def add_knowledge(self, number: int = 5, seed: Union[int, float, None] = None,
                      file_path: Union[str, Path, None] = None) -> None:
        """添加知识命题
        Args:
            number (int): 要添加的知识命题数量. 默认为5.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            file_path (Union[str, Path, None], optional): 知识命题文件路径. 默认为None.
        """
        assert number > 0, "知识命题数量必须大于0"
        # 1-20移除：移除随机种子设置
        # random.seed(seed)
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
        
    # 12-14新增：将初始化范围获取机和询问机和获取可及命题的函数分开
    def get_preparations(self) -> None:
        """
        该方法从可行的陈述命题组合出发，建立推理图，获得可达命题列表\n
        该方法初始化范围获取机.\n
        """
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
        self._statements = [i.state(self.temps) for i in self._chosen_group] # 陈述列表
        # 1-15新增：记录命题的难度
        # 1-29修改：改为记录命题难度的最高值
        self._statement_difficulties = max([i.difficulty for i in self._chosen_group])
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
        # 1-15新增：记录命题的难度
        # 1-28修改：引用问题难度参数
        # self._question_difficulties = self._asked_prop.difficulty
        self._question_difficulties = self._asked_prop.question_difficulty
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

    def get_answers(self, seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1) -> Dict[str, Any] | None:
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
        # 12-11修改：将答案信息记录到中间变量中
        answer_info = am.run()
        if answer_info is None:
            return None
        else:
            self.answer_info = answer_info
        ans_info = deepcopy(self.answer_info) # 12-11修订：复制一份答案信息
        str_options = {k: str(v) for k, v in self.answer_info[machines.OPTIONS].items()} # 将选项转换为字符串
        ans_info | {machines.OPTIONS: str_options} # 将选项转换为字符串后添加到答案信息中
        return ans_info

    def get_chain(self) -> str:
        """获取推理链

        Returns:
            str: 推理链
        """
        assert self._asked_prop is not None, "必须先执行ask()方法进行提问"

        reason_path = self.graph.backtrace(self._asked_prop)
        for i in self.ans_props:
            if i != self._asked_prop:
                reason_path = reason_path + self.graph.backtrace(i)

        # 11-30更新：计算推理链长度
        self.chain_length = len(reason_path)
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
        # return self._ask_all_machine.run()
        ask_res = self._ask_all_machine.run()
        if ask_res is None:
            return ask_res
        option_state = [i.state(self.temps) if isinstance(i, prop.Proposition) else str(i) for i in self._ask_all_machine._option_dict.values()]
        # 1-15新增：记录命题的难度
        # 1-28修改：将这类问题的难度修改为命题难度最大值
        self._question_difficulties = max([i.difficulty for i in self._ask_all_machine._option_dict.values() if isinstance(i, prop.Proposition)])
        choice_dict = {k: v for k, v in zip(ask_res["choices"].keys(), option_state)}
        new_ask_res = ask_res | {"choices": choice_dict}
        return new_ask_res
    
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
            self.get_preparations() # 12-14新增：将初始化范围获取机和询问机和获取可及命题的函数分开
            self.get_statements()
            self.ask_one(seed)
            self.set_value_range() # 设置值域
            answers = self.get_answers(seed)
            if answers is None:
                print("未能获取答案，跳过.")
                continue
            # 修改：先判定能否生成答案，再获取推理链
            self.ans_props = answers[machines.ANSWERPROP] # 将正确答案填入空中的命题
            chain = self.get_chain() # 修改：将正确答案填入空中的命题记录到中间变量中
            text = self.guide + COLON + SEMICOLON.join(self._statements)  # 题面文本，由引导语和陈述组成
            # 问题信息
            item = {
                        "guide": self.guide, 
                        "statement": self._statements, 
                        "text": text,
                        "question": self._ask_info[prop.SENTENCE], 
                        "choices": answers[machines.OPTIONS], 
                        # "answers": answers[machines.ANSWERS], 
                        "answers": answers[machines.ANSWERS], # 11-24更新：将键从answers改为choices
                        "chain": chain, 
                        # 11-24更新：增加提问命题的层级信息
                        "layer": self.graph.layer_query(self._asked_prop), 
                        # 11-24更新：增加提问命题的标签信息
                        "tag": self._asked_prop.typetag, 
                        # 11-30更新：增加推理链长度信息
                        # LEVEL: ask_level(self.chain_length, len(self._statements), len(answers[machines.OPTIONS]), len(self._knowledges), self.scene_level),
                        # 12-25更新：修复评级上的错误
                        # 1-15更新：增加问题中命题难度参数
                        # 1-15更新：增加已知条件中命题的难度参数
                        # LEVEL: ask_level(self.chain_length, len(self._statements), len(answers[machines.ANSWERS]), len(self._knowledges), self.scene_level, self._question_difficulties),
                        # LEVEL: ask_level(self.chain_length, self._statement_difficulties, len(answers[machines.ANSWERS]), len(self._knowledges), self.scene_level, self._question_difficulties),
                        # 1-20修订：采用知识难度参数计算难度
                        LEVEL: ask_level(self.chain_length, self._statement_difficulties, len(answers[machines.ANSWERS]), self._knowledge_difficulties, self.scene_level, self._question_difficulties),
                        # 12-13更新：增加各种辅助判断信息
                        CHAIN_LENGTH: self.chain_length, 
                        SCENE_TYPE: self.scene_type, 
                        INIT_NUM: len(self._init_props), 
                        KNOWLEDGE_NUM: len(self._knowledges), 
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
        # 1-20移除：移除随机种子设置
        # random.seed(seed)
        self._ask_correct = ask_correct # 设置询问机的询问模式
        self.get_all_props()
        question_list = []
        i = 0
        while len(question_list) < execute:
            i += 1
            print(f"开始第{i}次获取.")
            self.get_all_groups()
            self.get_preparations() # 12-14新增：将初始化范围获取机和询问机和获取可及命题的函数分开
            self.get_statements()
            ask_all_info = self.ask_all(seed)
            if ask_all_info is None:
                print("未能获取答案，跳过.")
                continue
            text = self.guide + COLON + SEMICOLON.join(self._statements)  # 题面文本，由引导语和陈述组成
            # 11-30更新：计算试题等级
            # level = ask_level(ask_all_info[machines.LENGTH], len(self._statements), len(ask_all_info[machines.CHOICES]), len(self._knowledges), self.scene_level)
            # 12-25更新：修复评级上的错误
            # 1-15更新：增加问题中的命题难度参数
            # 1-15更新：增加已知条件中的命题难度参数
            # level = ask_level(ask_all_info[machines.LENGTH], len(self._statements), len(ask_all_info[machines.ANSWERS]), len(self._knowledges), self.scene_level, self._question_difficulties)
            # level = ask_level(ask_all_info[machines.LENGTH], self._statement_difficulties, len(ask_all_info[machines.ANSWERS]), len(self._knowledges), self.scene_level, self._question_difficulties)
            # 1-20修订：采用知识难度参数计算难度
            level = ask_level(ask_all_info[machines.LENGTH], self._statement_difficulties, len(ask_all_info[machines.ANSWERS]), self._knowledge_difficulties, self.scene_level, self._question_difficulties)
            item = {
                "guide": self.guide,
                "statement": self._statements,
                "text": text,
            } | ask_all_info | {
                LEVEL: level, 
                CHAIN_LENGTH: ask_all_info[machines.LENGTH], 
                SCENE_TYPE: self.scene_type, 
                INIT_NUM: len(self._init_props), 
                KNOWLEDGE_NUM: len(self._knowledges), 
            }
            question_list.append(item)
        print(f"获取题目{i}次，获得题目{len(question_list)}个.")
        return question_list