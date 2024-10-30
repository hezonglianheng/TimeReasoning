# encoding: utf8
# date: 2024-08-25
# author: Qin Yuhang

"""
定义命题推理规则和3元推理规则的标准写法
提供供调用和继承的基础命题推理规则
"""

import abc
from typing import Optional
import sys
from pathlib import Path
# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop

class Rule(metaclass = abc.ABCMeta):
    """命题推理规则的抽象基类"""
    # 命题推理规则涉及到的类名。其中，最后一个类名为推理结果的类型，之前的类名为条件的类名
    _rule_tuple: tuple[type[prop.Proposition]] = tuple()

    @classmethod
    @abc.abstractmethod
    def reason(cls, *props: prop.Proposition) -> Optional[prop.Proposition]:
        """根据命题推理生成新的命题

        Args:
            *props (Proposition): 输入的命题

        Returns:
            Optional[prop.Proposition]: 新的命题或者None
        """
        pass

    @classmethod
    def _assert_condition(cls, *props: prop.Proposition) -> bool:
        """判断传入条件与规则是否相符的辅助函数

        Returns:
            bool: 传入条件与每条规则是否相符
        """
        if len(cls._rule_tuple) - len(props) != 1:
            return False
        return all([isinstance(i, j) for i, j in zip(props, cls._rule_tuple)])

    @classmethod
    @abc.abstractmethod
    def judge(cls, dst: prop.Proposition, *props: prop.Proposition) -> bool:
        """判断命题是否通过规则和前件推导出来\n

        Args:
            dst (Proposition): 待判断的命题
            *props (Proposition): 输入的命题

        Returns:
            bool: 是否符合规则
        """
        return cls.reason(*props) == dst

class TripleRule(Rule):
    """由2个前件和1个结论共同构成的3命题规则，来源于三段论，是最基础的推理形式"""
    _rule_tuple: tuple[type[prop.Proposition], type[prop.Proposition], type[prop.Proposition]] = tuple()

    @classmethod
    @abc.abstractmethod
    def reason(cls, prop1: prop.Proposition, prop2: prop.Proposition) -> Optional[prop.Proposition]:
        """根据命题推理生成新的命题\n
        开发者指南：若继承这个类，则可以在继承此方法之前，添加自己的筛选规则

        Args:
            prop1 (prop.Proposition): 输入的命题1
            prop2 (prop.Proposition): 输入的命题2

        Returns:
            Optional[prop.Proposition]: 新的命题或者None
        """
        assert len(cls._rule_tuple) == 3, "3命题规则要求规则中包含3个类名，其中，最后一个类名为推理结果的类型，之前的类名为条件的类名"

    @classmethod
    def judge(cls, dst: prop.Proposition, prop1: prop.Proposition, prop2: prop.Proposition) -> bool:
        """判断命题是否通过规则和前件推导出来\n

        Args:
            dst (Proposition): 待判断的命题
            prop1 (Proposition): 输入的命题1
            prop2 (Proposition): 输入的命题2

        Returns:
            bool: 是否符合规则
        """
        return cls.reason(prop1, prop2) == dst or cls.reason(prop2, prop1) == dst

class TransitivityRule(TripleRule):
    """
    类传递性规则\n
    推导方式: F(x, y) && G(y, z) -> H(x, z)
    """
    _rule_tuple: tuple[type[prop.DoubleProp], type[prop.DoubleProp], type[prop.DoubleProp]] = tuple()

    @classmethod
    def reason(cls, prop1: prop.DoubleProp, prop2: prop.DoubleProp) -> Optional[prop.DoubleProp]:
        super().reason(prop1, prop2)
        if not cls._assert_condition(prop1, prop2):
            return None
        if prop1.element2 == prop2.element1 and prop1.element1 != prop2.element2:
            res_ty = cls._rule_tuple[-1]
            return res_ty(prop1.element1, prop2.element2)
        else:
            return None
        
class TwoSingleToDoubleRule(TripleRule):
    """
    从两个单元素命题推出一个双元素命题的规则\n
    推导方式: F(x) && G(y) -> H(x, y)
    """
    _rule_tuple: tuple[type[prop.SingleProp], type[prop.SingleProp], type[prop.DoubleProp]] = tuple()

    @classmethod
    def reason(cls, prop1: prop.SingleProp, prop2: prop.SingleProp) -> Optional[prop.DoubleProp]:
        super().reason(prop1, prop2)
        if not cls._assert_condition(prop1, prop2):
            return None
        res_ty = cls._rule_tuple[-1]
        return res_ty(prop1.element, prop2.element)

class DoubleSingleToSingleRule(Rule):
    """
    从一个双元素命题和一个单元素命题推出一个单元素命题的规则\n
    推导方式: F(x, y) && G(x) -> H(y) 或者 F(x, y) && G(y) -> H(x)
    """
    _rule_tuple: tuple[type[prop.DoubleProp], type[prop.SingleProp], type[prop.SingleProp]] = tuple()

    @classmethod
    def reason(cls, prop1: prop.DoubleProp, prop2: prop.SingleProp) -> Optional[prop.SingleProp]:
        super().reason(prop1, prop2)
        if not cls._assert_condition(prop1, prop2):
            return None
        if prop1.element1 == prop2.element:
            res_ty = cls._rule_tuple[-1]
            return res_ty(prop1.element2)
        elif prop1.element2 == prop2.element:
            res_ty = cls._rule_tuple[-1]
            return res_ty(prop1.element1)
        else:
            return None

class DoubleAdd(TripleRule):
    """二元命题的加和规则\n
    推导方式: F(x, y) && G(x, y) -> H(x, y)
    """
    _rule_tuple: tuple[type[prop.DoubleProp], type[prop.DoubleProp], type[prop.DoubleProp]] = tuple()

    @classmethod
    def reason(cls, prop1: prop.DoubleProp, prop2: prop.DoubleProp) -> prop.DoubleProp | None:
        super().reason(prop1, prop2)
        if not cls._assert_condition(prop1, prop2):
            return None
        res_ty = cls._rule_tuple[-1]
        if prop1.element1 == prop2.element1 and prop1.element2 == prop2.element2:
            return res_ty(prop1.element1, prop1.element2)

# TODO: 需要考虑提供更多的推理规则，供外部开发者调用和继承