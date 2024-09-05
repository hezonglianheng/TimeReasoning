# encoding: utf8
# date: 2024-08-31
# author: Qin Yuhang

"""
关于命题中元素的基本抽象类定义
"""

import abc

class Element(metaclass = abc.ABCMeta):
    """命题中元素的抽象基类
    """
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        """判断两个元素是否相等的方法

        Args:
            other (object): 另一个元素

        Returns:
            bool: 是否相等
        """
        return type(self) == type(other)

    def __ne__(self, other: object) -> bool:
        """判断两个元素是否不相等，是__eq__的反向操作

        Args:
            other (object): 另一个元素

        Returns:
            bool: 是否不相等
        """
        return not self == other

    def __str__(self) -> str:
        return "" # 返回空字符串