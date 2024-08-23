# encoding: utf8
# date: 2024-08-20
# author: Qin Yuhang
# 用于调度时间常识知识库

import timescale as scale
import json5
from pathlib import Path
import abc
from typing import Any, Self, Literal, Callable
import random

KTYPE = Literal["point", "period"]

VERBOSE: int = 0 # 输出信息的详细程度

# 时间常识知识库文件名称
__KNOWLEDGE_FILES = {
    scale.TimeScale.Year: "year.json5",
    scale.TimeScale.Order: "order.json5",
}

KNOWLEDGE_LIST: list[str] = []

def get_knowledge_dict(scale: scale.TimeScale) -> dict:
    """获取时间常识知识库

    Args:
        scale (stmt.TimeScale): 时间尺度

    Returns:
        dict: 时间常识知识库
    """
    file = Path(__file__).parent / "knowledge" / __KNOWLEDGE_FILES[scale]
    with open(file, "r", encoding="utf8") as f:
        return json5.load(f)

class Knowledge(metaclass=abc.ABCMeta):
    """时间常识库中知识的抽象基类"""
    @abc.abstractmethod
    def __init__(self):
        """初始化一条知识"""
        pass

    @abc.abstractmethod
    def apply(self, *args, **kwargs):
        """调用本条知识对陈述或问题等进行处理"""
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.apply(*args, **kwds)

def verbose(func: Callable[[Knowledge, str], str]) -> Callable[[Knowledge, str], str]:
    """输出信息的装饰器"""
    def wrapper(self: Knowledge, statement: str) -> str:
        if VERBOSE >= 1:
            if isinstance(self, PointKnowledge):
                print(f"调用知识：({self.time}年, {self.description})")
        if VERBOSE >= 2:
            KNOWLEDGE_LIST.append(f"({self.time}年, {self.description})")
        return func(self, statement)
    return wrapper
    
class PointKnowledge(Knowledge):
    """时间点知识类"""
    def __init__(self, time: int, description: str, scale: scale.TimeScale):
        """初始化一条时间点知识

        Args:
            time (int): 时间点
            description (str): 对于该知识的描述
            scale (stmt.TimeScale): 时间尺度
        """
        super().__init__()
        self.time = time
        self.description = description
        self.scale = scale

    @classmethod
    def from_dict(cls, d: dict[str, str], scale: scale.TimeScale) -> Self:
        """从时间-描述字典中创建一个时间点知识

        Args:
            d (dict[int, str]): 时间-描述字典

        Returns:
            PointKnowledge: 时间点知识
        """
        assert len(d) == 1, "字典长度不为1"
        time, description = d.popitem()
        return cls(int(time), description, scale)
    
    @verbose
    def apply(self, statement: str) -> str:
        """将statement中的时间点替换为描述

        Args:
            statement (str): 待处理的陈述

        Raises:
            ValueError: 不支持当前时间尺度时抛出

        Returns:
            str: 处理后的陈述
        """        """"""
        if self.scale is scale.TimeScale.Year:
            # 将statement中的时间点替换为描述
            new_stmt = statement.replace(f"{self.time}年", self.description)
            return new_stmt
        else:
            raise ValueError("不支持当前时间尺度")

    def __call__(self, statement: str) -> str:
        """将statement中的时间点替换为描述

        Args:
            statement (str): 待处理的陈述

        Returns:
            str: 处理后的陈述
        """
        return self.apply(statement)

class KnowledgeBase:
    """时间常识知识库类"""
    def __init__(self, scale: scale.TimeScale) -> None:
        """初始化时间常识知识库

        Args:
            scale (scale.TimeScale): 时间尺度
        """        
        self.scale = scale
        self.knowledge_list: list[Knowledge] = []
        self.__get_knowledge_list() # 读取知识列表

    def __get_knowledge_list(self):
        """从文件中读取知识列表"""
        knowledge_dict: dict[str, list[str]] = get_knowledge_dict(self.scale)
        for time, descriptions in knowledge_dict.items():
            self.knowledge_list.extend([PointKnowledge(int(time), desc, self.scale) for desc in descriptions])

    def add_knowledge(self, knowledge: Knowledge | dict[int, str]):
        """向知识库中添加临时的知识
        
        Args:
            knowledge (Knowledge | dict[int, str]): 要添加的知识
        """
        if isinstance(knowledge, dict):
            self.knowledge_list.append(PointKnowledge.from_dict(knowledge, self.scale))
        else:
            self.knowledge_list.append(knowledge)

    def apply(self, statement: str, ktype: KTYPE, **kwargs) -> str:
        """对陈述进行知识处理，返回处理后的陈述。若没有可用知识，则返回原陈述

        Args:
            statement (str): 待处理的陈述
            ktype (KTYPE): 知识类型
            **kwargs: 其他参数

        Returns:
            str: 处理后的陈述或原陈述
        """
        if ktype == "point":
            assert isinstance(t := kwargs.get("time"), int), "至少需要提供一个int类型的时间点"
            usable_knowledge = [k for k in self.knowledge_list if isinstance(k, PointKnowledge) and k.time == t]
            if not usable_knowledge:
                return statement # 没有可用知识，直接返回原陈述
            # 随机选择一条知识
            knowledge = random.choice(usable_knowledge)
            return knowledge(statement)
        elif ktype == "period":
            pass
        else:
            raise ValueError(f"未知知识类型{ktype}")