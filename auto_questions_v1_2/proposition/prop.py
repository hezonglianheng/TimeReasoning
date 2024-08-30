# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
关于命题的基本定义和基本操作
"""

import abc
import random
from typing import Dict, Any

# 返回的问题信息
SENTENCE = "sentence"
TYPE = "type"
ANSWER = "answer"

class Proposition(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, symmetrical: bool = False, precise: bool = False, askable: bool = False):
        """初始化命题

        Args:
            symmetrical (bool, optional): 是否对称. 默认为False.
            precise (bool, optional): 是否精确. 默认为False.
            askable (bool, optional): 是否可询问. 默认为False.
        """
        self.symmetrical = symmetrical
        self.precise = precise
        self.askable = askable

    @property
    @abc.abstractmethod
    def temp_key(self) -> str:
        """返回命题的模板关键词，为str"""
        return ""

    def attrs(self) -> dict[str, str]:
        """返回命题的属性，为dict[str, str]"""
        return {k: str(v) for k, v in vars(self).items()}
    
    def state(self, temps: dict[str, list[str]]) -> str:
        """返回命题的陈述，为str"""
        curr_temp = random.choice(temps[self.temp_key])
        for k, v in self.attrs().items():
            curr_temp = curr_temp.replace(f"[{k}]", v)
        return curr_temp

    def ask(self, temps: dict[str, list[str]], key: str = None) -> Dict[str, str | Any]:
        """返回命题的问题信息，为dict[str, str | Any]"""
        global SENTENCE, TYPE, ANSWER
        assert self.askable, "命题不可询问"
        curr_temp = random.choice(temps[self.temp_key])
        # q_key: str = key if key is not None else random.choice(list(self.attrs().keys()))
        q_key: str = key
        while q_key is None or f"[{q_key}]" not in curr_temp:
            q_key = random.choice(list(self.attrs().keys()))
        curr_ans = vars(self)[q_key]
        curr_dict = self.attrs() | {q_key: "____"}
        for k, v in curr_dict.items():
            curr_temp = curr_temp.replace(f"[{k}]", v)
        return {SENTENCE: curr_temp, TYPE: q_key, ANSWER: curr_ans}

    def __eq__(self, value: object) -> bool:
        """判断两个命题是否相等

        Args:
            value (object): 另一个命题

        Returns:
            bool: 两个命题是否相等
        """
        # 判断value的类与self的类是否相同，之后判断value的属性与self的属性是否相同
        return type(value) == type(self) and vars(self) == vars(value)
    
    def got(self, prop_list: list["Proposition"]) -> bool:
        """判断一个命题是否包含在一个命题列表中

        Args:
            prop_list (list[Proposition]): 命题列表

        Returns:
            bool: 一个命题是否包含在一个命题列表中
        """
        return any([self == prop for prop in prop_list])

# TODO: 按照主要元的不同定义Proposition的子类，以解耦领域和推理