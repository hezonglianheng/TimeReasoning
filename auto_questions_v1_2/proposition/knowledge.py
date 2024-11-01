# encoding: utf8
# date: 2024-10-28
# author: Qin Yuhang

"""
定义知识的抽象基类
"""

import abc
from typing import Any

class Knowledge(metaclass=abc.ABCMeta):
    """知识的抽象基类
    """
    def __init__(self) -> None:
        pass
    
    @abc.abstractmethod
    def use(self) -> Any:
        pass