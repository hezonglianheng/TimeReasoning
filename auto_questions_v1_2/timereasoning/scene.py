# encoding: utf8
# date: 2024-08-27
# author: Qin Yuhang

from copy import deepcopy
from typing import Any, Dict, Optional
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, relation
from timereasoning import timeprop, timerule, timerelation, event
from timereasoning import timescale as ts
from proposition.scene import Scene

class TimeScene(Scene):
    """
    时间场景
    """
    def __init__(self, scale: ts.TimeScale | int, guide: str = "") -> None:
        """初始化时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为"".
        """
        # 需要使用的属性
        super().__init__(guide)
        self.scale = scale if isinstance(scale, ts.TimeScale) else ts.TimeScale(scale) # 时间尺度
        self.events: list[event.Event] = [] # 事件列表
        self.relations = deepcopy(timerelation.RELATIONS) # 关系列表
        self.rules = deepcopy(timerule.RULES) # 规则列表
        self.temps = ts.choose_templates(scale)
        # 命题收集变量（为了安全性需要重新定义）
        self._init_props: list[timeprop.TimeP] = []
        self._all_props: list[timeprop.TimeP] = []
        self._all_groups: list[list[int]] = []
        self._statements: list[str] = []
        self._asked_prop: timeprop.TimeP = None
        self._ask_info: dict[str, Any] = {}
        self._value_range: dict[str, list[Any]] = dict()

    def add_events(self, *events: event.Event) -> None:
        """添加事件

        Args:
            events (Event): 待添加的事件
        """
        assert all([isinstance(i, event.Event) for i in events]), "事件列表必须为事件"
        assert all([not isinstance(i, (event.SubEvent, event.Duration)) for i in events]), "事件列表不能为子事件或持续时间"
        self.events.extend(events) # 将事件加入到事件列表中
        self._init_props.extend([timeprop.SingleTimeP.build(i) for i in events]) # 将事件转化为初始时间命题

    def ask(self, seed: int | float | None = None) -> Dict[str, Any]:
        info = super().ask(seed)
        all_elements = [i.element for i in self._all_props if isinstance(i, timeprop.SingleTimeP)]
        if "element" in (typ := info.get(prop.TYPE)):
            ans = info.get(prop.ANSWER)
            if isinstance(ans, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent)):
                self._value_range[typ] = [i for i in all_elements if isinstance(i, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent))]
            elif isinstance(ans, event.Duration):
                self._value_range[typ] = [i for i in all_elements if isinstance(i, (event.Duration, event.TemporalEvent, event.FreqEvent))]
            else:
                raise ValueError(f"未知类型{type(ans)}")
        elif "time" in typ:
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[0], all_temp[-1] + 1))
        elif typ == "duration":
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[-1] - all_temp[0] + 1))
        elif typ == "diff":
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[-1] - all_temp[0] + 1))
        return info

class LineScene(TimeScene):
    """
    线性时间场景
    """
    def __init__(self, scale: ts.TimeScale | int, guide: str = "") -> None:
        """初始化线性时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为空字符串.
        """
        super().__init__(scale, guide)

class LoopScene(TimeScene):
    """
    循环时间场景
    """
    def __init__(self, scale: ts.TimeScale | int, guide: str = "", loop: Optional[int] = None) -> None:
        super().__init__(scale, guide)
        self.loop = ts.get_loop_param(scale) if loop is None else loop
        assert self.loop is not None, "未知的循环长度"
        self.LoopRelation.loop = self.loop
        self.relations.append(self.LoopRelation) # 添加循环关系
    
    class LoopRelation(relation.Relation):
        """
        时间循环关系
        """
        loop = 0

        @classmethod
        def reason(cls, prop: timeprop.BeforeTimeP | timeprop.AfterTimeP) -> Optional[timeprop.TimeP]:
            if isinstance(prop, timeprop.BeforeTimeP):
                new_prop = timeprop.AfterTimeP(prop.element1, prop.element2, cls.loop - prop.diff)
                return [new_prop]
            elif isinstance(prop, timeprop.AfterTimeP):
                new_prop = timeprop.BeforeTimeP(prop.element1, prop.element2, cls.loop - prop.diff)
                return [new_prop]
            else:
                return None