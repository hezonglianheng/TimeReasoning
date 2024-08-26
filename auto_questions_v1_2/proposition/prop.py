# encoding: utf8
# date: 2024-08-24
# author: Qin Yuhang

"""
关于命题的基本定义和基本操作
"""

import abc

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

    @abc.abstractmethod
    def state(self) -> str:
        """返回命题的陈述，为str"""
        pass

    @abc.abstractmethod
    def ask(self) -> str:
        """返回命题的询问，为str"""
        assert self.askable, "命题不可询问"

    def __eq__(self, value: object) -> bool:
        """判断两个命题是否相等

        Args:
            value (object): 另一个命题

        Returns:
            bool: 两个命题是否相等
        """
        # 判断value的类与self的类是否相同，之后判断value的属性与self的属性是否相同
        return type(value) == type(self) and vars(self) == vars(value)