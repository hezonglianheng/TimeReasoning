# encoding: utf8
# date: 2024-12-31

"""
内部数据结构中元素的基本抽象类定义
"""

import abc
from typing import Any
import warnings
from collections.abc import Sequence

class Element(metaclass = abc.ABCMeta):
    """内部数据结构中元素的抽象基类，包含名称、类型和属性
    """
    def __init__(self, name: str = "", kind: str = "", **kwargs):
        """元素的构造函数

        Args:
            name (str, optional): 元素的名称，默认为"".
            kind (str, optional): 元素的类型，默认为"".
            **kwargs: 元素的其他属性
        """
        self.name: str = name # 元素的名称
        self.kind: str = kind # 元素的类型
        self.attrs: dict[str, Any] = kwargs # 元素的属性

    def kind_infer(self):
        """对元素的类型进行自动推断\n请注意自动推断未必准确
        """
        pass

    @abc.abstractmethod
    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        """将元素翻译成指定语言的方法

        Args:
            lang (str): 语言
            require (str, optional): 翻译的要求，默认为None.
            **kwargs: 翻译的其他参数

        Returns:
            str: 翻译结果
        """
        pass

    def __eq__(self, other: "Element") -> bool:
        """判断两个元素是否相等的方法

        Args:
            other (Element): 另一个元素

        Returns:
            bool: 是否相等
        """
        if not type(self) == type(other):
            raise TypeError(f"元素{self}和元素{other}类型不同，无法比较")
        if self.kind != other.kind:
            return False
        for key in self.attrs:
            if self[key] != other[key]:
                return False
        return True

    def __ne__(self, other: "Element") -> bool:
        return not self == other

    def __getitem__(self, key: str) -> Any:
        """获取元素的属性值，等价于attrs[key]

        Args:
            key (str): 属性名

        Returns:
            Any: 属性值
        """
        value = self.attrs.get(key)
        if value is None:
            raise KeyError(f"元素{self}没有属性'{key}'")
        return value
    
    def __setitem__(self, key: str, value: Any):
        """设置元素的属性值

        Args:
            key (str): 属性名
            value (Any): 属性值
        """
        # 如果属性已存在，发出警告
        if key in self.attrs:
            warnings.warn(f"属性'{key}'已存在，将被覆盖", UserWarning)
        self.attrs[key] = value

    def is_contained(self, element_list: list["Element"]) -> bool:
        """判断一个元素是否在一个元素集中

        Args:
            element_list (list[Element]): 元素集

        Returns:
            bool: 事件是否在元素集中的判定
        """
        return any([self == e for e in element_list])

    def __str__(self) -> str:
        return str(vars(self))

    def has_attr(self, key: str) -> bool:
        """判断元素是否有某个属性

        Args:
            key (str): 属性名

        Returns:
            bool: 是否有该属性
        """
        return key in self.attrs
    '''
    def __getattribute__(self, name: str) -> Any:
        """允许使用self.name的方式获取属性值

        Args:
            name (str): 属性名

        Returns:
            Any: 属性值
        """
        if name in ["name", "kind", "attrs"]:
            return super().__getattribute__(name)
        else:
            return self[name]

    def __setattr__(self, name: str, value: Any):
        """允许使用self.name的方式设置属性值

        Args:
            name (str): 属性名
            value (Any): 属性值
        """
        if name in ["name", "kind", "attrs"]:
            super().__setattr__(name, value)
        else:
            self[name] = value
    '''
def name_is_unique(elements: Sequence[Element]) -> bool:
    """判断元素的名称是否唯一

    Args:
        elements (Sequence[Element]): 元素序列

    Returns:
        bool: 名称是否唯一
    """
    name_set = set()
    for e in elements:
        if e.name in name_set:
            print(f"元素{e}的名称{e.name}不唯一")
            return False
        name_set.add(e.name)
    return True