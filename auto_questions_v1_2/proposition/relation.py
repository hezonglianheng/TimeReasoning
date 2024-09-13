# encoding: utf8
# date: 2024-08-25
# author: Qin Yuhang

"""
定义命题间关系的标准写法
根据命题的主要元个数，定义单元命题和双元命题的基础关系
"""

import abc
from typing import Optional, List
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop

class Relation(metaclass = abc.ABCMeta):
    """命题间关系的抽象基类"""
    # 具有某种命题间关系的命题类型对的列表，用于关系的推断
    _tp_tuples: list[tuple[type[prop.Proposition], type[prop.Proposition]]] = []
    
    @classmethod
    def add_props_tuples(cls, *tuples: tuple[type[prop.Proposition], type[prop.Proposition]]):
        """添加具有这一关系的两个命题的子类型二元元组，分别为类说明中提到的F和G
        
        Args:
            *tuples(tuple[type[prop.Proposition], type[prop.Proposition]]): 具有这一关系的两个命题的子类型元组
        """
        assert len(tuples) > 0, "元组不能为空"
        assert all([len(i) == 2 for i in tuples]), "元组中的元素必须为两个"
        cls._tp_tuples.extend(tuples)
    
    @classmethod
    @abc.abstractmethod
    def reason(cls, input_prop: prop.Proposition) -> Optional[List[prop.Proposition]]:
        """从一个命题推断具有某种关系的另一个命题

        Args:
            input_prop (prop.Proposition): 起始命题

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
        if any([prop2 == i for i in cls.reason(prop1)]):
            return True
        return False

class SingleRelation(Relation):
    """
    单元命题的关系
    """
    _tp_tuples: list[tuple[type[prop.SingleProp], type[prop.SingleProp]]] = []
    
    @classmethod
    def add_props_tuples(cls, *tuples: tuple[type[prop.SingleProp], type[prop.SingleProp]]):
        assert all([(issubclass(prop.SingleProp), i) for i in tuples]), "元组中的元素必须为单元命题"
        return super().add_props_tuples(*tuples)

class DoubleRelation(Relation):
    """
    双元命题的关系
    """
    _tp_tuples: list[tuple[type[prop.DoubleProp], type[prop.DoubleProp]]] = []
    
    @classmethod
    def add_props_tuples(cls, *tuples: tuple[type[prop.DoubleProp], type[prop.DoubleProp]]):
        assert all([issubclass(i[0], prop.DoubleProp) and issubclass(i[1], prop.DoubleProp) for i in tuples]), "元组中的元素必须为双元命题"
        return super().add_props_tuples(*tuples)

class SingleEquivalence(SingleRelation):
    """
    单元命题的等价关系\n
    数学形式为: F(x) <-> G(x)
    """
    _tp_tuples: list[tuple[type[prop.SingleProp], type[prop.SingleProp]]] = []

    @classmethod
    def reason(cls, input_prop: prop.SingleProp) -> Optional[List[prop.SingleProp]]:
        if not isinstance(input_prop, prop.SingleProp):
            return None
        res: list[prop.SingleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(input_prop.element))
            if isinstance(input_prop, tp2):
                res.append(tp1(input_prop.element))
        return res

class DoubleEquivalence(DoubleRelation):
    """
    双元命题的等价关系\n
    数学形式为: F(x, y) <-> G(x, y)
    """
    _tp_tuples: list[tuple[type[prop.DoubleProp], type[prop.DoubleProp]]] = []
    
    @classmethod
    def reason(cls, input_prop: prop.DoubleProp) -> Optional[List[prop.DoubleProp]]:
        if not isinstance(input_prop, prop.DoubleProp):
            return None
        res: list[prop.DoubleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(input_prop.element1, input_prop.element2))
            if isinstance(input_prop, tp2):
                res.append(tp1(input_prop.element1, input_prop.element2))
        return res

class DoubleReverseEq(DoubleRelation):
    """
    双元命题的对称关系\n
    数学形式为: F(x, y) <-> G(y, x)
    """
    _tp_tuples: list[tuple[type[prop.DoubleProp], type[prop.DoubleProp]]] = []

    @classmethod
    def reason(cls, input_prop: prop.DoubleProp) -> Optional[List[prop.DoubleProp]]:
        if not isinstance(input_prop, prop.DoubleProp):
            return None
        res: list[prop.DoubleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(element1=input_prop.element2, element2=input_prop.element1))
            if isinstance(input_prop, tp2):
                res.append(tp1(element1=input_prop.element2, element2=input_prop.element1))
        return res

class SingleEntailment(SingleRelation):
    """
    单元命题的蕴含关系\n
    数学形式为: F(x) -> G(x)
    """
    _tp_tuples: list[tuple[type[prop.SingleProp], type[prop.SingleProp]]] = []
    
    @classmethod
    def reason(cls, input_prop: prop.SingleProp) -> Optional[List[prop.SingleProp]]:
        if not isinstance(input_prop, prop.SingleProp):
            return None
        res: list[prop.SingleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(input_prop.element))
        return res

class DoubleEntailment(DoubleRelation):
    """
    双元命题的蕴含关系\n
    数学形式为: F(x, y) -> G(x, y)
    """
    _tp_tuples: list[tuple[type[prop.DoubleProp], type[prop.DoubleProp]]] = []
    
    @classmethod
    def reason(cls, input_prop: prop.DoubleProp) -> List[prop.DoubleProp] | None:
        if not isinstance(input_prop, prop.DoubleProp):
            return None
        res: list[prop.SingleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(input_prop.element1, input_prop.element2))
        return res

class DoubleReverseEn(DoubleRelation):
    """
    双元命题的对称蕴含关系\n
    数学形式为: F(x, y) -> G(y, x)
    """
    _tp_tuples: list[tuple[type[prop.DoubleProp], type[prop.DoubleProp]]] = []
    
    @classmethod
    def reason(cls, input_prop: prop.DoubleProp) -> List[prop.DoubleProp] | None:
        if not isinstance(input_prop, prop.DoubleProp):
            pass
        res: list[prop.SingleProp] = []
        for tp1, tp2 in cls._tp_tuples:
            if isinstance(input_prop, tp1):
                res.append(tp2(input_prop.element2, input_prop.element1))
        return res

class Conflict(Relation):
    """命题的冲突关系，待实现
    """
    pass

if __name__ == "__main__":
    e = SingleEquivalence()