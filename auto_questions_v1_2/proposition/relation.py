# encoding: utf8
# date: 2024-08-25
# author: Qin Yuhang

import abc
from typing import Optional, List
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop

class Relation(metaclass = abc.ABCMeta):
    tp_tuples: list[tuple[type[prop.Proposition], type[prop.Proposition]]] = []
    
    @classmethod
    def add_props_tuples(cls, *tuples: tuple[type[prop.Proposition], type[prop.Proposition]]):
        """添加具有这一关系的两个命题的子类型元组
        
        Args:
            *tuples(tuple[type[prop.Proposition], type[prop.Proposition]]): 具有这一关系的两个命题的子类型元组
        """
        cls.tp_tuples.extend(tuples)
    
    @classmethod
    @abc.abstractmethod
    def reason(cls, prop: prop.Proposition) -> Optional[List[prop.Proposition]]:
        """从一个命题推断具有某种关系的另一个命题

        Args:
            prop (prop.Proposition): 起始命题

        Returns:
            Optional[List[prop.Proposition]]: 推断出的命题列表
        """
        pass

    @classmethod
    def judge(cls, prop1: prop.Proposition, prop2: prop.Proposition) -> bool:
        """判断两个命题是否具有该命题关系

        Args:
            prop1 (prop.Proposition): 第一个命题
            prop2 (prop.Proposition): 第二个命题

        Returns:
            bool: 两个命题是否具有这一关系
        """
        # if cls.reason(prop1) == prop2:
        if any([prop2 == i for i in cls.reason(prop1)]):
            return True
        return False

class Equivalence(Relation):
    @classmethod
    def reason(cls, prop: prop.Proposition) -> Optional[prop.Proposition]:
        pass

class Entailment(Relation):
    @classmethod
    def reason(cls, prop: prop.Proposition) -> Optional[prop.Proposition]:
        pass

class Conflict(Relation):
    @classmethod
    def reason(cls, prop: prop.Proposition) -> prop.Proposition:
        pass

if __name__ == "__main__":
    e = Equivalence()