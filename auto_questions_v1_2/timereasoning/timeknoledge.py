# encoding: utf8
# date: 2024-10-28
# author: Qin Yuhang

import sys
import abc
from pathlib import Path
import random

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

# 引入事件类型描述事件常识
import timereasoning.event as event
# 引入命题类型表示事件先后常识
import timereasoning.timeprop as timeprop

class Knowledge(metaclass = abc.ABCMeta):
    """表示时间常识的抽象基类"""
    pass

class EventKnowledge(Knowledge):
    """表示事件常识的抽象基类"""
    pass

class OrderKnowledge(Knowledge):
    """表示时间顺序常识的抽象基类"""
    pass

