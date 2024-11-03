# encoding: utf8
# date: 2024-10-28
# author: Qin Yuhang

import json5
import sys
import abc
from pathlib import Path
from typing import Literal, Any

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.knowledge as know
# 引入事件类型描述事件常识
import timereasoning.event as event
# 引入命题类型表示事件先后常识
import timereasoning.timeprop as timeprop
# 时间尺度决定调用哪一个时间常识库
import timereasoning.timescale as timescale

class TimeKnowledge(know.Knowledge):
    """表示时间常识的抽象基类"""
    def __init__(self):
        pass
    
    @classmethod
    def build(cls, typ: Literal["event", "order", "convert"], dic: dict) -> "TimeKnowledge":
        """根据类型和字典构造时间常识对象的工厂方法

        Args:
            typ (Literal[&quot;event&quot;, &quot;order&quot;, &quot;convert&quot;]): 知识的类型
            dic (dict): 知识的字典

        Raises:
            ValueError: 时间常识的类型不正确

        Returns:
            Knowledge: 时间常识对象
        """
        if typ == "event":
            return EventKnowledge(dic)
        elif typ == "order":
            return OrderKnowledge(dic)
        elif typ == "convert":
            return ConvertKnowledge(dic)
        else:
            raise ValueError(f"时间常识的类型{typ}不正确")

class EventKnowledge(TimeKnowledge):
    """表示事件常识的类"""
    def __init__(self, dic: dict[str, Any]):
        """初始化事件常识

        Args:
            dic (dict[str, Any]): 事件知识的字典
        """
        self.dic = dic
        self.event = self._check_subtype()

    def _check_subtype(self) -> event.Event:
        """检查事件知识的subtype标签是否正确，根据subtype标签构造事件对象并返回
        
        Returns:
            timereasoning.event.Event: 事件对象

        Raises:
            ValueError: 事件知识的subtype标签不正确
        """
        if "subtype" not in self.dic:
            raise ValueError(f"事件知识{self.dic}没有subtype标签")
        if self.dic["subtype"] == "temporal":
            curr_dict = {k: v for k, v in self.dic.items() if k in ["verb", "object", "time"]}
            return event.TemporalEvent(**curr_dict)
        elif self.dic["subtype"] == "durative":
            curr_dict = {k: v for k, v in self.dic.items() if k in ["verb", "object", "time", "endtime"]}
            return event.DurativeEvent(**curr_dict)
        elif self.dic["subtype"] == "freq":
            curr_dict = {k: v for k, v in self.dic.items() if k in ["verb", "object", "time", "endtime", "frequency"]}
            return event.FreqEvent(**curr_dict)
        else:
            raise ValueError(f"事件知识的subtype标签{self.dic["subtype"]}不正确")

    def use(self) -> timeprop.SingleTimeP:
        """使用事件常识的方法，返回事件对应的不可提问时间命题"""
        prop = timeprop.SingleTimeP.build(self.event, askable=False)
        return prop

class OrderKnowledge(TimeKnowledge):
    """表示时间顺序常识的类"""
    def use(self):
        """使用时间顺序常识的方法"""
        pass

class ConvertKnowledge(TimeKnowledge):
    """表示时间转换常识的类"""
    def use(self):
        """使用时间转换常识的方法"""
        pass

def get_knowledge_base(scale: timescale.TimeScale | int) -> list[TimeKnowledge]:
    """根据时间尺度获取时间常识库

    Args:
        scale (timescale.TimeScale|int): 时间尺度

    Returns:
        list[Knowledge]: 时间常识库
    """
    scale = timescale.TimeScale(scale) if isinstance(scale, int) else scale
    know_dir = Path(__file__).resolve().parent / "knowledge"
    all_knows: list[TimeKnowledge] = []
    with open(know_dir / f"{scale.name.lower()}.json5", "r", encoding="utf-8") as f:
        know_dict: dict[Literal["event", "order", "convert"], list] = json5.load(f)
        for typ, knows in know_dict.items():
            for know in knows:
                all_knows.append(TimeKnowledge.build(typ, know))
    return all_knows

def add_knowledge(scale: timescale.TimeScale):
    """添加时间常识库中成员的函数，待开发

    Args:
        scale (timescale.TimeScale): 时间尺度
    """
    pass