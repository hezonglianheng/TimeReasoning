# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
关于命题的基本定义和基本操作
本文件中定义了命题的抽象类、一元命题、二元命题和三元命题
"""

import abc
import random
from typing import Dict, Any
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.element as element
import proposition.config as config

# 返回的问题信息
SENTENCE = "sentence"
TYPE = "type"
ANSWER = "answer"

class Proposition(element.Element):
    """命题的抽象基类"""
    @abc.abstractmethod
    def __init__(self, askable: bool = True, precise: bool = True):
        """初始化命题

        Args:
            askable (bool, optional): 是否可询问. 默认为True.
            precise (bool, optional): 是否精确. 默认为True.
        """
        self.askable = askable # 是否可询问
        self.precise = precise # 是否精确
        # 1-15新增：命题的难度等级
        self.difficulty: float = 1.0 # 难度等级，默认为1
        # 1-28新增：命题的问题难度等级，默认与命题的难度等级相同
        self.question_difficulty: float = self.difficulty

    @property
    def num_of_conditions(self) -> int:
        """返回命题的可推出条件数量，为int"""
        return 1

    @property
    @abc.abstractmethod
    def temp_key(self) -> str:
        """返回命题的模板关键词，为str"""
        return ""

    def attrs(self) -> dict[str, str]:
        """返回命题以字符串形式表达的属性
        
        Returns: 
            dict[str, str]: 属性字典
        """
        return {k: str(v) for k, v in vars(self).items()}
    
    def state(self, temps: dict[str, list[str]]) -> str:
        """返回命题的陈述
        
        Args:
            temps (dict[str, list[str]]): 模板字典，从中选取对应的模板

        Returns:
            str: 命题的一个陈述句
        """
        curr_temp = random.choice(temps[self.temp_key])
        # for k, v in self.attrs().items():
        for k, v in vars(self).items():
            curr_temp = curr_temp.replace(f"[{k}]", str(v))
        return curr_temp

    def ask(self, temps: dict[str, list[str]], key: str = None) -> Dict[str, str | Any]:
        """返回命题的问题信息
        
        Args:
            temps (dict[str, list[str]]): 模板字典，从中选取对应的模板
            key (str): 可以指定询问的字段. 默认为None(不指定).

        Returns:
            Dict[str, str | Any]: 问题的题面、字段、正确答案等信息
        """
        global SENTENCE, TYPE, ANSWER
        assert self.askable, "命题不可询问"
        curr_temp = random.choice(temps[self.temp_key])
        q_key: str = key
        while q_key is None or f"[{q_key}]" not in curr_temp:
            q_key = random.choice(list(self.attrs().keys()))
        curr_ans = vars(self)[q_key]
        curr_dict = self.attrs() | {q_key: config.ASK_POINT}
        for k, v in curr_dict.items():
            curr_temp = curr_temp.replace(f"[{k}]", v)
        # 计算命题的问题难度等级：增加下划线索引与SENTENCE长度的比例值相关的反比例函数
        # 1-29新增：考虑下划线索引的中间值
        # 1-31新增：将下划线影响改为2
        self.question_difficulty = self.difficulty + 2 * (1 - (curr_temp.index(config.ASK_POINT) + 2) / len(curr_temp))
        return {SENTENCE: curr_temp, TYPE: q_key, ANSWER: curr_ans}

    def __eq__(self, other: object) -> bool:
        """判断两个命题是否相等，本质上是判断两个命题的类型和属性是否相等

        Args:
            value (object): 另一个命题

        Returns:
            bool: 两个命题是否相等
        """
        return super().__eq__(other) and self.askable == other.askable and self.precise == other.precise
    
    def __ne__(self, value: object) -> bool:
        """判断两个命题是否不相等，本质上是判断两个命题的类型和属性是否不相等

        Args:
            value (object): 另一个命题

        Returns:
            bool: 两个命题是否不相等
        """
        return not self == value
    
    def got(self, prop_list: list["Proposition"]) -> bool:
        """判断一个命题是否包含在一个命题列表中

        Args:
            prop_list (list[Proposition]): 命题列表

        Returns:
            bool: 一个命题是否包含在一个命题列表中
        """
        return any([self == prop for prop in prop_list])

    def contained(self, prop_list: list["Proposition"]) -> bool:
        """判断时间命题的可推出条件是否包含在命题列表中

        Args:
            prop_list (list[prop.Proposition]): 命题列表

        Returns:
            bool: 时间命题是否包含在命题列表中
        """
        return any([i == self for i in prop_list])

    @property
    @abc.abstractmethod
    def typetag(self) -> str:
        """返回命题的类型标签，为str"""
        return ""

    # 1-17添加：一个验证函数，用于验证命题的合法性
    def sancheck(self) -> bool:
        """验证命题的合理性

        Returns:
            bool: 命题是否合理
        """
        return True

# 按照主要元个数的不同定义Proposition的子类，以解耦领域和推理

class SingleProp(Proposition):
    """
    一元命题，是有1个主要元的命题。它相当于一个一元函数。\n
    例如：命题“星期五召开课题组会议”确定了一个主要元“召开课题组会议”(x)的位置，可以形式化为InFriday(x)，是个一元命题。
    """
    def __init__(self, element1: element.Element, askable: bool = True, precise: bool = True):
        super().__init__(askable, precise)
        self.element = element1

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.element == other.element

class DoubleProp(Proposition):
    """
    二元命题，是有2个主要元的命题。它相当于一个二元函数。\n
    例如：命题“当她来到舞厅时，她的心上人已经离开了”确定了两个主要元“她来到舞厅”(x)和“她的心上人离开”(y)的关系，可以形式化为Before(y, x)，是个二元命题。
    """
    def __init__(self, element1: element.Element, element2: element.Element, askable: bool = True, precise: bool = True):
        super().__init__(askable, precise)
        self.element1 = element1
        self.element2 = element2

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.element1 == other.element1 and self.element2 == other.element2

    # 1-17添加：一个验证函数，用于验证命题的合理性
    def sancheck(self) -> bool:
        """验证2元命题的合理性，即两个元素不能相等

        Returns:
            bool: 命题是否合理
        """
        return self.element1 != self.element2

class TripleProp(Proposition):
    def __init__(self, element1: element.Element, element2: element.Element, element3: element.Element, askable: bool = True, precise: bool = True):
        super().__init__(askable, precise)
        self.element1 = element1
        self.element2 = element2
        self.element3 = element3

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.element1 == other.element1 and self.element2 == other.element2 and self.element3 == other.element3

    # 1-17添加：一个验证函数，用于验证命题的合理性
    def sancheck(self) -> bool:
        """验证3元命题的合法性，即元素不能相等

        Returns:
            bool: 命题是否合理
        """
        return self.element1 != self.element2 and self.element1 != self.element3 and self.element2 != self.element3