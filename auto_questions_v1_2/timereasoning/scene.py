# encoding: utf8
# date: 2024-08-27
# author: Qin Yuhang

from pycnnum import num2cn # 引入中文数字转换库
import re
from copy import deepcopy
from typing import Any, Dict, Optional, Union
import sys
from pathlib import Path
import random

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, relation
from timereasoning import timeprop, timerule, timerelation, event
from timereasoning import timescale as ts
from proposition.scene import Scene
from timereasoning import timeknoledge # 10-30修改：开始引入时间常识库
from timereasoning.machines import SearchMachine as SM # 11-03修改：引入时间领域专用搜索机

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

    def add_knowledge(self, number: int = 5, seed: Union[int, float, None] = None) -> None:
        """添加时间常识

        Args:
            number (int, optional): 添加的常识数量. 默认为5.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
        """
        super().add_knowledge(number, seed)
        know_list = timeknoledge.get_knowledge_base(self.scale)
        chosen_know = random.sample(know_list, number) if number < len(know_list) else know_list
        print(f"实际添加时间常识{len(chosen_know)}个.")
        for k in chosen_know: # 遍历所有的时间常识
            if isinstance(k, timeknoledge.EventKnowledge): # 如果是事件常识
                self._knowledges.append(k.use()) # 将事件转化为时间命题
            else:
                pass # 其他类型的常识暂不处理，后续可以添加
    
    def reset(self):
        """清空场景中的事件"""
        self.events.clear()
        self._init_props.clear()
    
    def _statement_trans(self):
        """
        调整语句中的时间表达方式\n
        例如，将星期几的数字转化为中文
        """
        if self.scale == ts.TimeScale.Weekday: # 如果是星期尺度，可以做一些特殊的处理
            for n in range(len(self._statements)):
                search1 = re.search(r"星期[0-9]", self._statements[n])
                if search1 is not None:
                    ch_num = num2cn(search1.group()[-1])
                    self._statements[n] = self._statements[n].replace(search1.group(), "星期" + ch_num)
                search2 = re.search(r"周[0-9]", self._statements[n])
                if search2 is not None:
                    ch_num = num2cn(search2.group()[-1])
                    self._statements[n] = self._statements[n].replace(search2.group(), "周" + ch_num)
        else:
            pass

    # 11-03修改：在时间领域重载获取全部命题的方法
    def get_all_groups(self) -> None:
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始搜索一组可行的命题组合.")
        sm = SM(self.events, self._all_props)
        self._chosen_group = sm.run()
        print(f"命题组合搜索结束.")

    def get_statements(self) -> list[str]:
        super().get_statements()
        self._statement_trans()
        return self._statements
    
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
        new_relations = list(map(lambda x: x.set_loop(self.loop), [LoopRelation, PeriodRelation, DiffRelation]))
        self.relations.extend(new_relations) # 添加特有的关系
        self.rules.remove(timerule.BeforeandGap)
        self.rules.remove(timerule.AfterandGap) # 移除不适用的规则
    
    def get_all_props(self) -> None:
        super().get_all_props()
        for i in self._all_props:
            if isinstance(i, timeprop.TemporalP):
                i.time = i.time % self.loop
            elif isinstance(i, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)):
                i.diff = i.diff % self.loop
        new_list: list[timeprop.TimeP] = list()
        for i in range(len(self._all_props)):
            if self._all_props[i].got(self._all_props[:i]):
                continue
            elif isinstance(self._all_props[i], (timeprop.BeforeP, timeprop.AfterP, timeprop.LongP, timeprop.ShortP)):
                continue
            # 增加命题去除条件：若命题是BeforeTimeP, AfterTimeP, GapTimeP且diff为0，则去除
            elif isinstance(self._all_props[i], (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)) and self._all_props[i].diff == 0:
                continue
            else:
                new_list.append(self._all_props[i])
        print(f"调整后有命题{len(new_list)}个.")
        self._all_props = new_list

class PeriodRelation(relation.SingleEntailment):
    """表示时间点的周期性关系，属于单元蕴含关系"""
    loop = 0
    _tp_tuples = [(timeprop.TemporalP, timeprop.TemporalP)]

    @classmethod
    def reason(cls, input_prop: timeprop.TemporalP) -> list[timeprop.TemporalP] | None:
        if not isinstance(input_prop, timeprop.TemporalP):
            return None
        res = super().reason(input_prop)
        if res is None:
            return None
        else:
            for i in res:
                i.time = i.time % cls.loop
            return res

    @classmethod
    def set_loop(cls, loop: int) -> type["PeriodRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls

class DiffRelation(relation.DoubleEntailment):
    """表示时间差的周期性关系，属于双元蕴含关系"""
    loop = 0
    _tp_tuples = [(timeprop.BeforeTimeP, timeprop.BeforeTimeP), (timeprop.AfterTimeP, timeprop.AfterTimeP), (timeprop.GapTimeP, timeprop.GapTimeP)]

    @classmethod
    def reason(cls, input_prop: timeprop.DoubleTimeP) -> list[timeprop.DoubleTimeP] | None:
        if not isinstance(input_prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)):
            return None
        res = super().reason(input_prop)
        if res is None:
            return None
        else:
            for i in res:
                i.diff = i.diff % cls.loop
            return res
        
    @classmethod
    def set_loop(cls, loop: int) -> type["DiffRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls
    
class LoopRelation(relation.DoubleEntailment):
    """循环关系，用于处理先后关系的循环性质"""
    loop = 0
    _tp_tuples = [(timeprop.BeforeTimeP, timeprop.AfterTimeP), (timeprop.AfterTimeP, timeprop.BeforeTimeP)]

    @classmethod
    def reason(cls, prop: timeprop.BeforeTimeP | timeprop.AfterTimeP) -> list[timeprop.BeforeTimeP | timeprop.AfterTimeP] | None:
        if not isinstance(prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP)):
            return None
        res = super().reason(prop)
        if res is None:
            return None
        else:
            for i in res:
                i.diff = cls.loop - prop.diff
            return res

    @classmethod
    def set_loop(cls, loop: int) -> type["LoopRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls
